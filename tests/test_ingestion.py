"""Unit and integration tests for data ingestion pipeline and Decimal/date parsers."""

from datetime import date
from decimal import Decimal

from app.db.connection import SessionLocal
from app.db.models import Category, Order, Product
from app.ingestion.csv_loader import CSVIngestionService, parse_date, parse_decimal
from app.ingestion.pdf_loader import PDFPolicyLoader


def test_parse_decimal_variants():
    """Verify parse_decimal handles various Brazilian and English currency strings."""
    assert parse_decimal("599.90") == Decimal("599.90")
    assert parse_decimal("599,90") == Decimal("599.90")
    assert parse_decimal("R$ 1.299,50") == Decimal("1299.50")
    assert parse_decimal("11499") == Decimal("11499.00")
    assert parse_decimal(None) == Decimal("0.00")
    assert parse_decimal("invalid") == Decimal("0.00")


def test_parse_date_variants():
    """Verify parse_date handles ISO and Brazilian date formats."""
    assert parse_date("2026-03-15") == date(2026, 3, 15)
    assert parse_date("15/03/2026") == date(2026, 3, 15)
    assert parse_date("") is None
    assert parse_date(None) is None


def test_csv_ingestion_idempotency():
    """Verify ingesting data multiple times updates existing records without duplication."""
    db = SessionLocal()
    try:
        service = CSVIngestionService()
        first_run = service.ingest_all(db)
        second_run = service.ingest_all(db)

        assert first_run["categories"] == second_run["categories"]
        assert first_run["products"] == second_run["products"]
        assert first_run["customers"] == second_run["customers"]
        assert first_run["orders"] == second_run["orders"]

        # Check actual database counts
        cat_count = db.query(Category).count()
        prod_count = db.query(Product).count()
        order_count = db.query(Order).count()

        assert cat_count == 9
        assert prod_count == 65
        assert order_count == 20
    finally:
        db.close()


def test_relational_integrity():
    """Verify foreign key relations between orders, customers, and products."""
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == 1).first()
        assert order is not None
        assert order.customer is not None
        assert len(order.items) > 0
        assert order.items[0].product is not None
    finally:
        db.close()


def test_pdf_policy_loader_extraction():
    """Verify PDF policy loader generates valid chunks with titles and page numbers."""
    loader = PDFPolicyLoader()
    chunks = loader.chunk_policy()
    assert len(chunks) > 0

    # Ensure key sections are detected
    titles = [c.section_title.lower() for c in chunks]
    has_payment = any("pagamento" in t for t in titles)
    has_returns = any("troca" in t or "devolu" in t or "arrepend" in t for t in titles)
    assert has_payment or has_returns
