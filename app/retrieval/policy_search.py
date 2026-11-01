"""BM25-based policy retrieval system for store policies."""

import re
from typing import Any

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.connection import SessionLocal
from app.db.models import PolicyDocument
from app.ingestion.pdf_loader import PDFPolicyLoader, PolicyChunk


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric terms for BM25 indexing."""
    return re.findall(r"\w+", text.lower())


class PolicySearchService:
    """Provides keyword-based BM25 search over store policy sections."""

    def __init__(self, db: Session | None = None):
        self.db = db
        self.chunks: list[PolicyChunk] = []
        self.bm25: BM25Okapi | None = None
        self._initialize_index()

    def _initialize_index(self) -> None:
        """Load policy documents from SQLite or directly from PDF, and build BM25 index."""
        # 1. Try loading from SQLite
        session = self.db or SessionLocal()
        close_session = self.db is None
        try:
            records = session.query(PolicyDocument).all()
            if records:
                self.chunks = [
                    PolicyChunk(
                        section_number=r.section_number,
                        section_title=r.section_title,
                        page_number=r.page_number,
                        content=r.content,
                    )
                    for r in records
                ]
                logger.info(f"Loaded {len(self.chunks)} policy chunks from SQLite database.")
        except Exception as e:
            logger.warning(
                f"Could not load policy documents from DB ({e}), trying direct PDF extraction..."
            )
        finally:
            if close_session:
                session.close()

        # 2. Fallback to direct PDF parsing if database table was empty
        if not self.chunks:
            loader = PDFPolicyLoader()
            self.chunks = loader.chunk_policy()

        # 3. Build BM25 Okapi index
        if self.chunks:
            corpus = [tokenize(f"{c.section_title} {c.content}") for c in self.chunks]
            self.bm25 = BM25Okapi(corpus)
            logger.info("BM25 Policy index built successfully.")
        else:
            logger.warning("PolicySearchService initialized with an empty corpus.")

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Retrieve the top-k most relevant policy sections for a given query."""
        if not self.bm25 or not self.chunks:
            return []

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        scored_pairs = list(enumerate(scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        results: list[dict[str, Any]] = []
        for idx, score in scored_pairs[:top_k]:
            if score <= 0:
                continue
            chunk = self.chunks[idx]
            results.append(
                {
                    "section_number": chunk.section_number,
                    "section_title": chunk.section_title,
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                    "score": round(float(score), 4),
                }
            )

        logger.debug(f"Query '{query}' returned {len(results)} policy results.")
        return results

    def format_evidence(self, results: list[dict[str, Any]]) -> str:
        """Format retrieved policy sections into structured, cited text."""
        if not results:
            return "Nenhuma seção relevante encontrada no manual de políticas."

        formatted_snippets = []
        for r in results:
            sec_header = f"Seção: {r['section_title']} (Página {r['page_number']})"
            formatted_snippets.append(f"### {sec_header}\n{r['content']}")

        return "\n\n".join(formatted_snippets)
