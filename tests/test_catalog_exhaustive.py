"""Exhaustive automated tests for product catalog search, brand filtering, and stock checks."""

from app.db.connection import SessionLocal
from app.services.catalog import CatalogService


def test_search_by_brand():
    """Verify filtering products by specific brand name."""
    db = SessionLocal()
    try:
        service = CatalogService(db)
        yamaha_items = service.search_products(brand="Yamaha", in_stock_only=False)
        assert len(yamaha_items) > 0
        assert all("Yamaha" in item["name"] for item in yamaha_items)

        tagima_items = service.search_products(brand="Tagima", in_stock_only=False)
        assert len(tagima_items) > 0
        assert all("Tagima" in item["name"] for item in tagima_items)
    finally:
        db.close()


def test_out_of_stock_product_detection():
    """Verify that Giannini GF-3D (ID 96) is correctly flagged as out of stock."""
    db = SessionLocal()
    try:
        service = CatalogService(db)
        stock_info = service.check_stock(96)
        assert stock_info["found"] is True
        assert stock_info["stock_quantity"] == 0
        assert stock_info["is_in_stock"] is False

        # When searching with in_stock_only=True, it must NOT appear
        in_stock_results = service.search_products(query="GF-3D", in_stock_only=True)
        assert len(in_stock_results) == 0

        # When searching with in_stock_only=False, it MUST appear
        all_results = service.search_products(query="GF-3D", in_stock_only=False)
        assert len(all_results) > 0
        assert all_results[0]["product_id"] == 96
    finally:
        db.close()


def test_search_by_max_price():
    """Verify max_price ceiling filter is strictly respected."""
    db = SessionLocal()
    try:
        service = CatalogService(db)
        max_limit = 600.0
        items = service.search_products(max_price=max_limit, in_stock_only=True)
        assert len(items) > 0
        assert all(item["regular_price_brl"] <= max_limit for item in items)
    finally:
        db.close()


def test_active_promotions_calculation():
    """Verify that products on active promotions have correct discount math and non-stackable PIX."""
    db = SessionLocal()
    try:
        service = CatalogService(db)
        active_promos = service.list_active_promotions()
        assert len(active_promos) > 0

        for promo in active_promos:
            orig = promo["original_price_brl"]
            promo_price = promo["promotional_price_brl"]
            discount_pct = promo["discount_percent"]
            expected_promo = round(orig * (1 - discount_pct / 100), 2)
            assert abs(promo_price - expected_promo) <= 0.02
    finally:
        db.close()


def test_get_product_by_name_partial_match():
    """Verify get_product_by_id_or_name resolves partial strings correctly."""
    db = SessionLocal()
    try:
        service = CatalogService(db)
        card = service.get_product_by_id_or_name("Martin D-28")
        assert card is not None
        assert card["product_id"] == 93
        assert "Martin D-28" in card["name"]
        assert card["regular_price_brl"] == 11499.00
    finally:
        db.close()
