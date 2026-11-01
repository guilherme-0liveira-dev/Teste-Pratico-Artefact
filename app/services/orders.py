"""Order service for tracking purchase status and details."""

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Customer, Order, Product


class OrderService:
    """Service to look up order status, fulfillment tracking, and purchased items."""

    def __init__(self, db: Session):
        self.db = db

    def get_order_status(
        self,
        order_id: int,
        customer_verification: str | None = None,
    ) -> dict[str, Any]:
        """Look up order details with optional customer identity verification."""
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return {
                "found": False,
                "message": f"Pedido #{order_id} não foi encontrado no sistema.",
            }

        customer: Customer = order.customer

        # Verification check (if verification string is provided, verify match)
        if customer_verification:
            verif_clean = customer_verification.strip().lower()
            name_match = verif_clean in customer.name.lower()
            email_match = verif_clean in customer.email.lower()
            phone_match = customer.phone and verif_clean in customer.phone.lower()

            if not (name_match or email_match or phone_match):
                return {
                    "found": True,
                    "verified": False,
                    "message": (
                        f"Pedido #{order_id} encontrado, mas os dados de verificação informados não conferem. "
                        "Por favor, confirme seu e-mail cadastrado ou nome completo para visualização dos detalhes."
                    ),
                }

        # Build items list
        items_detail = []
        for item in order.items:
            product: Product = item.product
            items_detail.append(
                {
                    "product_id": product.product_id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "unit_price_brl": float(product.price_decimal),
                }
            )

        status_pt = {
            "delivered": "Entregue",
            "shipped": "Em transporte / Despachado",
            "confirmed": "Pagamento confirmado (em separação)",
            "pending": "Aguardando confirmação de pagamento",
            "cancelled": "Cancelado",
        }.get(order.status, order.status)

        status_explanation = {
            "delivered": "Seu pedido foi entregue com sucesso.",
            "shipped": f"Seu pedido está a caminho. Rastreamento: {order.tracking_code or 'Consulte suporte'}. Previsão: {order.estimated_delivery or 'Em breve'}.",
            "confirmed": "Seu pagamento foi confirmado! O instrumento está em fase de separação e embalagem.",
            "pending": "Aguardando confirmação do pagamento junto à instituição financeira.",
            "cancelled": f"Este pedido foi cancelado. Observação: {order.notes or 'Cancelamento solicitado'}.",
        }.get(order.status, "")

        return {
            "found": True,
            "verified": True,
            "order_id": order.order_id,
            "customer_name": customer.name,
            "customer_city": customer.city,
            "order_date": str(order.order_date),
            "status": order.status,
            "status_display": status_pt,
            "status_explanation": status_explanation,
            "total_brl": float(order.total_decimal),
            "payment_method": order.payment_method,
            "tracking_code": order.tracking_code,
            "estimated_delivery": str(order.estimated_delivery)
            if order.estimated_delivery
            else None,
            "notes": order.notes,
            "items": items_detail,
        }
