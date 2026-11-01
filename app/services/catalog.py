"""Catalog service for querying products, checking inventory, and resolving promotional pricing."""

from decimal import Decimal
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Category, Product, Promotion
from app.services.business_rules import (
    calculate_pix_discount,
    get_max_allowed_installments,
)


class CatalogService:
    """Service to search, filter, and inspect products in the Empório da Música catalog."""

    def __init__(self, db: Session):
        self.db = db

    def search_products(
        self,
        query: str | None = None,
        category: str | None = None,
        brand: str | None = None,
        max_price: float | Decimal | None = None,
        in_stock_only: bool = True,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search products matching the given criteria and compute their pricing terms."""
        stmt = self.db.query(Product).join(Category)

        if in_stock_only:
            stmt = stmt.filter(Product.stock_quantity > 0, Product.status == "active")

        if query:
            clean_q = f"%{query.strip()}%"
            stmt = stmt.filter(
                or_(
                    Product.name.ilike(clean_q),
                    Product.description.ilike(clean_q),
                    Category.name.ilike(clean_q),
                )
            )

        if category:
            clean_cat = f"%{category.strip()}%"
            stmt = stmt.filter(Category.name.ilike(clean_cat))

        if brand:
            clean_brand = f"%{brand.strip()}%"
            stmt = stmt.filter(Product.name.ilike(clean_brand))

        if max_price is not None:
            max_dec = Decimal(str(max_price))
            stmt = stmt.filter(Product.price_brl <= max_dec)

        stmt = stmt.order_by(Product.price_brl.asc()).limit(limit)
        products = stmt.all()

        results: list[dict[str, Any]] = []
        for p in products:
            results.append(self._format_product_card(p))

        return results

    def get_product_by_id_or_name(self, identifier: str | int) -> dict[str, Any] | None:
        """Fetch exact product by ID or close name match."""
        product = None
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            product = self.db.query(Product).filter(Product.product_id == int(identifier)).first()

        if not product and isinstance(identifier, str):
            clean_id = f"%{identifier.strip()}%"
            product = self.db.query(Product).filter(Product.name.ilike(clean_id)).first()

        if not product:
            return None

        return self._format_product_card(product)

    def check_stock(self, identifier: str | int) -> dict[str, Any]:
        """Check availability and stock count for a product."""
        p_card = self.get_product_by_id_or_name(identifier)
        if not p_card:
            return {
                "found": False,
                "message": f"Produto '{identifier}' não encontrado no catálogo.",
            }

        return {
            "found": True,
            "product_id": p_card["product_id"],
            "name": p_card["name"],
            "stock_quantity": p_card["stock_quantity"],
            "is_in_stock": p_card["is_in_stock"],
            "status": p_card["status"],
            "price_brl": p_card["final_price_brl"],
        }

    def list_active_promotions(self) -> list[dict[str, Any]]:
        """List all active promotions and their discounted products."""
        active_promos = (
            self.db.query(Promotion)
            .filter(Promotion.is_active == True)  # noqa: E712
            .all()
        )
        results: list[dict[str, Any]] = []
        for promo in active_promos:
            product = promo.product
            orig_price = product.price_decimal
            discount_pct = promo.discount_decimal
            promo_price = (orig_price * (Decimal("1") - discount_pct / Decimal("100"))).quantize(
                Decimal("0.01")
            )

            results.append(
                {
                    "promotion_id": promo.promotion_id,
                    "promotion_name": promo.description,
                    "discount_percent": float(discount_pct),
                    "product_id": product.product_id,
                    "product_name": product.name,
                    "category": product.category.name,
                    "original_price_brl": float(orig_price),
                    "promotional_price_brl": float(promo_price),
                    "stock_quantity": product.stock_quantity,
                    "in_stock": product.is_in_stock,
                }
            )
        return results

    def _format_product_card(self, p: Product) -> dict[str, Any]:
        """Enrich a Product ORM instance with active discounts, PIX price, and installments."""
        regular_price = p.price_decimal

        # Check if product has an active promotion
        active_promo = (
            self.db.query(Promotion)
            .filter(Promotion.product_id == p.product_id, Promotion.is_active == True)  # noqa: E712
            .first()
        )

        has_promo = active_promo is not None
        if has_promo:
            discount_pct = active_promo.discount_decimal
            promo_price = (regular_price * (Decimal("1") - discount_pct / Decimal("100"))).quantize(
                Decimal("0.01")
            )
            final_price = promo_price
            promo_name = active_promo.description
        else:
            discount_pct = Decimal("0.00")
            promo_price = regular_price
            final_price = regular_price
            promo_name = None

        # PIX calculation (5% discount on regular price, not cumulative with promotions)
        pix_price, pix_discount = calculate_pix_discount(regular_price, is_promotional=has_promo)

        # Max allowed installment
        best_inst = get_max_allowed_installments(final_price)

        return {
            "product_id": p.product_id,
            "name": p.name,
            "category": p.category.name if p.category else "Instrumentos",
            "regular_price_brl": float(regular_price),
            "final_price_brl": float(final_price),
            "has_promotion": has_promo,
            "promotion_name": promo_name,
            "promotion_discount_percent": float(discount_pct) if has_promo else None,
            "pix_price_brl": float(pix_price),
            "pix_discount_brl": float(pix_discount),
            "stock_quantity": p.stock_quantity,
            "is_in_stock": p.is_in_stock,
            "status": p.status,
            "max_installments": (
                f"{best_inst.installments}x de R$ {best_inst.monthly_amount:.2f} sem juros"
                if best_inst
                else "À vista"
            ),
            "description": p.description,
            "specs": p.specs,
        }
