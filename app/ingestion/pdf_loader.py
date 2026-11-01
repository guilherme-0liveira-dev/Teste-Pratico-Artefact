"""PDF policy extraction and chunking pipeline using PyMuPDF and pypdf fallback."""

import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models import PolicyDocument


@dataclass
class PolicyChunk:
    """Represents a discrete semantic chunk of the store policy manual."""

    section_number: str | None
    section_title: str
    page_number: int
    content: str


class PDFPolicyLoader:
    """Extracts, parses, and chunks the store policy manual with section attribution."""

    def __init__(self, pdf_path: Path | None = None):
        self.pdf_path = pdf_path or settings.POLICY_PDF_PATH
        if not self.pdf_path.exists():
            # Check fallback in root directory
            root_candidate = settings.BASE_DIR / self.pdf_path.name
            if root_candidate.exists():
                self.pdf_path = root_candidate

    def extract_raw_pages(self) -> list[tuple[int, str]]:
        """Extract plain text page-by-page. Attempts PyMuPDF first, falls back to pypdf."""
        if not self.pdf_path.exists():
            logger.warning(f"Policy PDF not found at {self.pdf_path}")
            return []

        pages: list[tuple[int, str]] = []
        try:
            import pymupdf as fitz

            doc = fitz.open(str(self.pdf_path))
            for page_idx in range(len(doc)):
                text = doc[page_idx].get_text()
                pages.append((page_idx + 1, text))
            logger.info(f"Extracted {len(pages)} pages using PyMuPDF from {self.pdf_path.name}")
            return pages
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed ({e}), falling back to pypdf...")

        try:
            import pypdf

            reader = pypdf.PdfReader(str(self.pdf_path))
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                # Normalize excessive whitespace from pypdf
                clean_text = re.sub(r"\s+", " ", text).strip()
                pages.append((idx + 1, clean_text))
            logger.info(f"Extracted {len(pages)} pages using pypdf from {self.pdf_path.name}")
            return pages
        except Exception as ex:
            logger.error(f"Failed to extract PDF text with both extractors: {ex}")
            return []

    def chunk_policy(self) -> list[PolicyChunk]:
        """Split extracted pages into discrete, attributable policy chunks."""
        raw_pages = self.extract_raw_pages()
        if not raw_pages:
            return []

        chunks: list[PolicyChunk] = []

        # Regex to detect major headings (e.g. '1. Sobre a...', '3.1 Regras de Parcelamento', etc.)
        section_pattern = re.compile(
            r"(?:\n|^)(\d+(?:\.\d+)*)\.?\s+([A-ZÀ-Ú][A-Za-zÀ-ú0-9\s,–—()-]{3,50})(?:\n|$)"
        )

        for page_num, text in raw_pages:
            # Clean header and footer repetitions
            cleaned = text.replace("Empório da Música Manual de Políticas e Procedimentos", "")
            cleaned = re.sub(r"Página\s+\d+", "", cleaned)

            lines = cleaned.split("\n")
            current_section_num: str | None = None
            current_section_title = f"Página {page_num}"
            current_buffer: list[str] = []

            for line in lines:
                trimmed = line.strip()
                if not trimmed:
                    continue

                match = section_pattern.match(trimmed)
                if match:
                    # Save previous buffer as chunk if non-empty
                    if current_buffer:
                        content_str = " ".join(current_buffer).strip()
                        if len(content_str) > 30:
                            chunks.append(
                                PolicyChunk(
                                    section_number=current_section_num,
                                    section_title=current_section_title,
                                    page_number=page_num,
                                    content=content_str,
                                )
                            )
                        current_buffer = []

                    current_section_num = match.group(1)
                    current_section_title = f"{match.group(1)} {match.group(2).strip()}"
                else:
                    current_buffer.append(trimmed)

            if current_buffer:
                content_str = " ".join(current_buffer).strip()
                if len(content_str) > 30:
                    chunks.append(
                        PolicyChunk(
                            section_number=current_section_num,
                            section_title=current_section_title,
                            page_number=page_num,
                            content=content_str,
                        )
                    )

        # Fallback if regex chunking was too aggressive or produced 0 chunks: page-level chunking
        if not chunks:
            for page_num, text in raw_pages:
                clean_text = " ".join(text.split()).strip()
                if clean_text:
                    chunks.append(
                        PolicyChunk(
                            section_number=None,
                            section_title=f"Políticas - Página {page_num}",
                            page_number=page_num,
                            content=clean_text,
                        )
                    )

        logger.info(f"Generated {len(chunks)} policy chunks from PDF.")
        return chunks

    def ingest_to_db(self, db: Session) -> int:
        """Persist extracted policy chunks into the SQLite database."""
        chunks = self.chunk_policy()
        if not chunks:
            logger.warning("No policy chunks to store in DB.")
            return 0

        db.query(PolicyDocument).delete()
        for c in chunks:
            db.add(
                PolicyDocument(
                    section_number=c.section_number,
                    section_title=c.section_title,
                    page_number=c.page_number,
                    content=c.content,
                )
            )
        db.commit()
        logger.info(f"Persisted {len(chunks)} policy chunks to SQLite table 'policy_documents'.")
        return len(chunks)
