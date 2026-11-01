"""Exhaustive automated tests for order status retrieval and identity verification."""

from app.db.connection import SessionLocal
from app.services.orders import OrderService


def test_order_status_delivered():
    """Verify delivered order status and tracking code."""
    db = SessionLocal()
    try:
        service = OrderService(db)
        res = service.get_order_status(1)
        assert res["found"] is True
        assert res["status"] == "delivered"
        assert res["status_display"] == "Entregue"
        assert res["tracking_code"] == "BRAB1234567BR"
        assert len(res["items"]) > 0
    finally:
        db.close()


def test_order_status_shipped():
    """Verify shipped in-transit order status."""
    db = SessionLocal()
    try:
        service = OrderService(db)
        res = service.get_order_status(8)
        assert res["found"] is True
        assert res["status"] == "shipped"
        assert (
            "a caminho" in res["status_explanation"].lower()
            or "rastreamento" in res["status_explanation"].lower()
        )
    finally:
        db.close()


def test_order_status_cancelled_with_notes():
    """Verify cancelled orders retain cancellation explanation in notes."""
    db = SessionLocal()
    try:
        service = OrderService(db)
        res = service.get_order_status(17)
        assert res["found"] is True
        assert res["status"] == "cancelled"
        assert "cancelado" in res["notes"].lower()
    finally:
        db.close()


def test_order_customer_verification_success():
    """Verify customer verification matches when email or name is provided."""
    db = SessionLocal()
    try:
        service = OrderService(db)
        # Order 1 belongs to customer Pedro Henrique Oliveira (pedro.oliveira@jmail.com)
        res_email = service.get_order_status(1, customer_verification="pedro.oliveira@jmail.com")
        assert res_email["verified"] is True

        res_name = service.get_order_status(1, customer_verification="Pedro Henrique")
        assert res_name["verified"] is True
    finally:
        db.close()


def test_order_customer_verification_failure():
    """Verify customer verification rejects mismatched credentials."""
    db = SessionLocal()
    try:
        service = OrderService(db)
        res = service.get_order_status(1, customer_verification="estranho@email.com")
        assert res["found"] is True
        assert res["verified"] is False
        assert "não conferem" in res["message"]
    finally:
        db.close()
