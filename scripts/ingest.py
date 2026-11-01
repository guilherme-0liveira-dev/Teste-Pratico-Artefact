"""Database initialization and full ingestion CLI script."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging import logger
from app.db.connection import SessionLocal, init_db
from app.ingestion.csv_loader import CSVIngestionService
from app.ingestion.pdf_loader import PDFPolicyLoader
from app.retrieval.policy_search import PolicySearchService


def run_ingestion() -> None:
    """Run table migrations, CSV data import, and PDF policy indexing."""
    print("=" * 60)
    print(" Empório AI — Data & Policy Ingestion Pipeline")
    print("=" * 60)

    # 1. Initialize DB tables
    init_db()

    db = SessionLocal()
    try:
        # 2. Ingest CSV operational datasets
        print("\n[1/3] Ingesting CSV datasets...")
        csv_service = CSVIngestionService()
        csv_summary = csv_service.ingest_all(db)
        for entity, count in csv_summary.items():
            print(f"  -> {entity.capitalize()}: {count} records loaded.")

        # 3. Ingest PDF Store Policy Manual
        print("\n[2/3] Extracting and indexing store policy manual...")
        pdf_loader = PDFPolicyLoader()
        policy_count = pdf_loader.ingest_to_db(db)
        print(f"  -> Policy Chunks: {policy_count} sections indexed.")

        # 4. Verify BM25 Indexing
        print("\n[3/3] Verifying BM25 policy retrieval index...")
        search_service = PolicySearchService(db=db)
        test_queries = [
            "formas de pagamento pix",
            "direito de arrependimento",
            "horario de funcionamento",
        ]
        for q in test_queries:
            results = search_service.search(q, top_k=1)
            if results:
                print(
                    f"  -> Query '{q}' matched: '{results[0]['section_title']}' (Score: {results[0]['score']})"
                )
            else:
                print(f"  -> Query '{q}' returned no results!")

        print("\n" + "=" * 60)
        print(" Ingestion completed successfully! Database is ready.")
        print("=" * 60)

    except Exception as e:
        logger.exception(f"Ingestion failed with error: {e}")
        print(f"\n[ERROR] Ingestion failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_ingestion()
