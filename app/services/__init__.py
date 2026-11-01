"""Domain services package."""

from app.services.business_rules import (
    calculate_installments,
    calculate_pix_discount,
    calculate_shipping,
    evaluate_return_eligibility,
    get_max_allowed_installments,
)
from app.services.catalog import CatalogService
from app.services.orders import OrderService

__all__ = [
    "CatalogService",
    "OrderService",
    "calculate_pix_discount",
    "calculate_installments",
    "get_max_allowed_installments",
    "evaluate_return_eligibility",
    "calculate_shipping",
]
