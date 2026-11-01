"""Tool definitions and schemas for the Empório AI agent."""

from collections.abc import Callable
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.db.connection import SessionLocal
from app.retrieval.policy_search import PolicySearchService
from app.services.business_rules import (
    calculate_installments,
    calculate_pix_discount,
    calculate_shipping,
    evaluate_return_eligibility,
)
from app.services.catalog import CatalogService
from app.services.orders import OrderService

# ============================================================================
# Pydantic Schemas for Tool Arguments
# ============================================================================


class SearchProductsInput(BaseModel):
    query: str | None = Field(
        default=None,
        description="Palavra-chave ou modelo (ex.: 'violão folk', 'Yamaha', 'estudante').",
    )
    category: str | None = Field(
        default=None,
        description="Categoria do instrumento (ex.: 'Violões', 'Guitarras', 'Teclados e Pianos', 'Baterias e Percussão').",
    )
    brand: str | None = Field(
        default=None,
        description="Marca do instrumento (ex.: 'Yamaha', 'Tagima', 'Giannini', 'Crafter', 'Takamine').",
    )
    max_price: float | None = Field(
        default=None, description="Preço máximo em Reais (ex.: 1000.00)."
    )
    in_stock_only: bool = Field(
        default=True, description="Se True, retorna apenas instrumentos disponíveis em estoque."
    )


class ProductDetailsInput(BaseModel):
    product_id_or_name: str = Field(
        description="ID do produto (ex.: 81) ou nome aproximado do instrumento (ex.: 'Yamaha C40')."
    )


class CheckStockInput(BaseModel):
    product_id_or_name: str = Field(
        description="ID do produto ou nome do modelo para checar disponibilidade e quantidade em estoque."
    )


class OrderStatusInput(BaseModel):
    order_id: int = Field(description="Número identificador do pedido (ex.: 1, 8, 15).")
    customer_verification: str | None = Field(
        default=None,
        description="E-mail ou nome do cliente para verificação de identidade (opcional).",
    )


class ActivePromotionsInput(BaseModel):
    pass


class PricingAndInstallmentsInput(BaseModel):
    product_id_or_name: str = Field(
        description="ID ou nome do instrumento para detalhar opções de parcelamento no cartão e valor à vista no PIX."
    )


class ShippingEstimateInput(BaseModel):
    order_total: float = Field(description="Valor total da compra em Reais (ex.: 650.00).")
    destination_city: str = Field(
        default="Campo Grande",
        description="Cidade de destino (ex.: 'Campo Grande', 'Dourados', 'São Paulo').",
    )


class StorePolicySearchInput(BaseModel):
    query: str = Field(
        description="Pergunta ou tema sobre as políticas da loja (ex.: 'direito de arrependimento 7 dias', 'horário de funcionamento', 'garantia de instrumentos', 'formas de pagamento', 'troca por defeito')."
    )


class ReturnEligibilityInput(BaseModel):
    days_since_delivery: int = Field(
        description="Quantidade de dias corridos decorridos desde que o cliente recebeu o produto."
    )
    is_online_purchase: bool = Field(
        default=True,
        description="Se a compra foi realizada online (True) ou presencialmente na loja (False).",
    )
    reason: str = Field(
        default="arrependimento",
        description="Motivo da devolução/troca: 'arrependimento', 'defeito', ou 'preferencia'.",
    )


# ============================================================================
# Tool Implementations
# ============================================================================


def execute_search_products(args: dict[str, Any]) -> str:
    """Search products in the catalog."""
    input_data = SearchProductsInput(**args)
    db = SessionLocal()
    try:
        service = CatalogService(db)
        items = service.search_products(
            query=input_data.query,
            category=input_data.category,
            brand=input_data.brand,
            max_price=input_data.max_price,
            in_stock_only=input_data.in_stock_only,
            limit=10,
        )
        if not items:
            return "Nenhum instrumento encontrado com os critérios informados. Sugira ao cliente ampliar a busca ou verificar outras categorias."

        output = [f"Encontrados {len(items)} instrumento(s):"]
        for p in items:
            promo_info = (
                f" [PROMOÇÃO: {p['promotion_name']} - {p['promotion_discount_percent']}% OFF]"
                if p["has_promotion"]
                else ""
            )
            stock_info = (
                f"Estoque: {p['stock_quantity']} un." if p["is_in_stock"] else "FORA DE ESTOQUE"
            )
            output.append(
                f"- ID {p['product_id']}: **{p['name']}** ({p['category']})\n"
                f"  Preço: R$ {p['final_price_brl']:.2f}{promo_info} | À vista no PIX: R$ {p['pix_price_brl']:.2f} (5% off)\n"
                f"  Parcelamento: {p['max_installments']} | {stock_info}"
            )
        return "\n".join(output)
    finally:
        db.close()


def execute_get_product_details(args: dict[str, Any]) -> str:
    """Get full details of a specific product."""
    input_data = ProductDetailsInput(**args)
    db = SessionLocal()
    try:
        service = CatalogService(db)
        p = service.get_product_by_id_or_name(input_data.product_id_or_name)
        if not p:
            return f"Instrumento '{input_data.product_id_or_name}' não encontrado no catálogo da Empório da Música."

        promo_text = (
            f"Sim ({p['promotion_name']} com {p['promotion_discount_percent']}% de desconto)"
            if p["has_promotion"]
            else "Não"
        )
        return (
            f"**Detalhes do Instrumento:**\n"
            f"- **Nome:** {p['name']}\n"
            f"- **Categoria:** {p['category']}\n"
            f"- **Preço Normal:** R$ {p['regular_price_brl']:.2f}\n"
            f"- **Preço Atual:** R$ {p['final_price_brl']:.2f} (Promoção: {promo_text})\n"
            f"- **Valor no PIX (5% off sobre preço regular):** R$ {p['pix_price_brl']:.2f}\n"
            f"- **Condições no Cartão:** {p['max_installments']}\n"
            f"- **Estoque Disponível:** {p['stock_quantity']} unidades ({'Em estoque' if p['is_in_stock'] else 'Indisponível'})\n"
            f"- **Descrição:** {p['description']}\n"
            f"- **Especificações:** {p['specs']}"
        )
    finally:
        db.close()


def execute_check_stock(args: dict[str, Any]) -> str:
    """Check stock and availability."""
    input_data = CheckStockInput(**args)
    db = SessionLocal()
    try:
        service = CatalogService(db)
        res = service.check_stock(input_data.product_id_or_name)
        if not res["found"]:
            return res["message"]
        if res["is_in_stock"]:
            return f"O produto **{res['name']}** (ID: {res['product_id']}) está **DISPONÍVEL** com {res['stock_quantity']} unidade(s) em estoque. Preço atual: R$ {res['price_brl']:.2f}."
        else:
            return f"O produto **{res['name']}** (ID: {res['product_id']}) está **TEMPORARIAMENTE INDISPONÍVEL** (estoque zerado). Recomende ao cliente modelos equivalentes disponíveis."
    finally:
        db.close()


def execute_get_order_status(args: dict[str, Any]) -> str:
    """Look up order fulfillment status."""
    input_data = OrderStatusInput(**args)
    db = SessionLocal()
    try:
        service = OrderService(db)
        res = service.get_order_status(input_data.order_id, input_data.customer_verification)
        if not res["found"]:
            return res["message"]
        if not res.get("verified", True):
            return res["message"]

        items_summary = "\n".join(
            [
                f"  - {it['quantity']}x {it['product_name']} (R$ {it['unit_price_brl']:.2f} cada)"
                for it in res["items"]
            ]
        )
        tracking_info = (
            f"Código de Rastreamento: `{res['tracking_code']}`"
            if res["tracking_code"]
            else "Código de Rastreamento: Não gerado ainda"
        )
        delivery_info = (
            f"Previsão de Entrega: {res['estimated_delivery']}"
            if res["estimated_delivery"]
            else "Previsão de Entrega: A definir"
        )

        return (
            f"**Informações do Pedido #{res['order_id']}**\n"
            f"- **Cliente:** {res['customer_name']} ({res['customer_city']})\n"
            f"- **Data do Pedido:** {res['order_date']}\n"
            f"- **Status Atual:** **{res['status_display']}** ({res['status']})\n"
            f"- **Situação:** {res['status_explanation']}\n"
            f"- **Forma de Pagamento:** {res['payment_method']}\n"
            f"- **Valor Total:** R$ {res['total_brl']:.2f}\n"
            f"- {tracking_info}\n"
            f"- {delivery_info}\n"
            f"- **Itens do Pedido:**\n{items_summary}"
        )
    finally:
        db.close()


def execute_get_active_promotions(args: dict[str, Any]) -> str:
    """List active store promotions."""
    db = SessionLocal()
    try:
        service = CatalogService(db)
        promos = service.list_active_promotions()
        if not promos:
            return "No momento não há promoções sazonais ativas no catálogo. Todos os instrumentos estão com preços regulares de tabela, com 5% de desconto à vista no PIX."

        output = ["**Promoções Ativas na Empório da Música:**"]
        for p in promos:
            stock_txt = f"{p['stock_quantity']} un. em estoque" if p["in_stock"] else "Esgotado"
            output.append(
                f"- **{p['product_name']}** ({p['category']}): De R$ {p['original_price_brl']:.2f} por **R$ {p['promotional_price_brl']:.2f}** "
                f"({p['discount_percent']}% OFF - {p['promotion_name']}) | Estoque: {stock_txt}"
            )
        output.append(
            "\n*Atenção: Conforme a política da loja, descontos de promoções não são cumulativos com o desconto de 5% do PIX.*"
        )
        return "\n".join(output)
    finally:
        db.close()


def execute_calculate_pricing_and_installments(args: dict[str, Any]) -> str:
    """Calculate exact payment terms, PIX discounts, and installment tiers."""
    input_data = PricingAndInstallmentsInput(**args)
    db = SessionLocal()
    try:
        service = CatalogService(db)
        p = service.get_product_by_id_or_name(input_data.product_id_or_name)
        if not p:
            return f"Instrumento '{input_data.product_id_or_name}' não encontrado."

        final_price = Decimal(str(p["final_price_brl"]))
        regular_price = Decimal(str(p["regular_price_brl"]))
        has_promo = p["has_promotion"]

        pix_price, pix_discount = calculate_pix_discount(regular_price, is_promotional=has_promo)
        installments = calculate_installments(final_price)

        allowed_lines = []
        rejected_lines = []
        for opt in installments:
            if opt.is_allowed:
                allowed_lines.append(
                    f"  - **{opt.installments}x** de **R$ {opt.monthly_amount:.2f}** sem juros (Total: R$ {opt.total_amount:.2f})"
                )
            else:
                rejected_lines.append(
                    f"  - {opt.installments}x de R$ {opt.monthly_amount:.2f}: {opt.explanation}"
                )

        promo_note = (
            f" (com desconto promocional de {p['promotion_discount_percent']}% - {p['promotion_name']})"
            if has_promo
            else ""
        )
        pix_explanation = (
            "Não aplicável porque o produto já possui desconto promocional ativo (regra de não-cumulatividade)."
            if has_promo
            else f"R$ {pix_price:.2f} (economize R$ {pix_discount:.2f} com 5% de desconto à vista)"
        )

        return (
            f"**Simulação de Pagamento para {p['name']}**\n"
            f"- **Preço Base Atual:** R$ {final_price:.2f}{promo_note}\n"
            f"- **Pagamento via PIX:** {pix_explanation}\n\n"
            f"**Opções de Parcelamento no Cartão de Crédito:**\n"
            + "\n".join(allowed_lines)
            + (
                "\n\n*Opções não permitidas pelas regras de parcela mínima:*\n"
                + "\n".join(rejected_lines)
                if rejected_lines
                else ""
            )
        )
    finally:
        db.close()


def execute_calculate_shipping_estimate(args: dict[str, Any]) -> str:
    """Calculate delivery fee and estimated delivery time."""
    input_data = ShippingEstimateInput(**args)
    res = calculate_shipping(Decimal(str(input_data.order_total)), input_data.destination_city)
    if res.is_local:
        if res.is_free_shipping:
            return (
                f"**Frete para {res.city}: FRETE GRÁTIS!**\n"
                f"- **Modalidade:** {res.delivery_method}\n"
                f"- **Prazo Estimado:** {res.estimated_days}\n"
                f"- **Observação:** {res.notes}"
            )
        else:
            return (
                f"**Frete para {res.city}: R$ {res.fee_brl:.2f}**\n"
                f"- **Modalidade:** {res.delivery_method}\n"
                f"- **Prazo Estimado:** {res.estimated_days}\n"
                f"- **Dica:** Pedidos a partir de R$ 500,00 contam com Frete Grátis na região de Campo Grande!"
            )
    else:
        return (
            f"**Frete para {res.city} (Fora da Grande Campo Grande):**\n"
            f"- **Modalidades disponíveis:** {res.delivery_method}\n"
            f"- **Prazos médios:** {res.estimated_days}\n"
            f"- **Cálculo do valor:** {res.notes}"
        )


def execute_search_store_policies(args: dict[str, Any]) -> str:
    """Search authoritative store policies in the internal manual."""
    input_data = StorePolicySearchInput(**args)
    searcher = PolicySearchService()
    results = searcher.search(input_data.query, top_k=2)
    return searcher.format_evidence(results)


def execute_evaluate_return_eligibility(args: dict[str, Any]) -> str:
    """Evaluate return or exchange eligibility deterministically."""
    input_data = ReturnEligibilityInput(**args)
    res = evaluate_return_eligibility(
        days_since_delivery=input_data.days_since_delivery,
        is_online_purchase=input_data.is_online_purchase,
        reason=input_data.reason,
    )
    status_str = "ELEGÍVEL" if res.is_eligible else "NÃO ELEGÍVEL"
    return (
        f"**Avaliação de Devolução / Troca: {status_str}**\n"
        f"- **Tipo:** {res.return_type}\n"
        f"- **Prazo Limite:** {res.deadline_days} dias corridos\n"
        f"- **Frete de Devolução:** {res.freight_covered_by}\n"
        f"- **Parecer:** {res.explanation}"
    )


# ============================================================================
# Tool Registry & JSON Schema Definitions for LLM
# ============================================================================

TOOL_REGISTRY: dict[str, Callable[[dict[str, Any]], str]] = {
    "search_products": execute_search_products,
    "get_product_details": execute_get_product_details,
    "check_product_stock": execute_check_stock,
    "get_order_status": execute_get_order_status,
    "get_active_promotions": execute_get_active_promotions,
    "calculate_pricing_and_installments": execute_calculate_pricing_and_installments,
    "calculate_shipping_estimate": execute_calculate_shipping_estimate,
    "search_store_policies": execute_search_store_policies,
    "evaluate_return_eligibility": execute_evaluate_return_eligibility,
}

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Busca instrumentos no catálogo da Empório da Música filtrando por texto, categoria, marca, preço máximo e disponibilidade de estoque.",
            "parameters": SearchProductsInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Consulta ficha técnica completa, preço regular, preço promocional, desconto PIX e especificações de um instrumento musical.",
            "parameters": ProductDetailsInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_product_stock",
            "description": "Verifica disponibilidade e quantidade exata em estoque para um instrumento.",
            "parameters": CheckStockInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Consulta o status de um pedido do cliente (entrega, rastreamento, itens, data e valor).",
            "parameters": OrderStatusInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_promotions",
            "description": "Lista todas as promoções e campanhas ativas no momento na loja com respectivos produtos e descontos.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_pricing_and_installments",
            "description": "Calcula de forma exata todas as opções de parcelamento permitidas no cartão e o valor com desconto de 5% no PIX.",
            "parameters": PricingAndInstallmentsInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_shipping_estimate",
            "description": "Calcula valor e prazo do frete com base no valor da compra e cidade do cliente (Regra de frete grátis acima de R$ 500 em Campo Grande).",
            "parameters": ShippingEstimateInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_store_policies",
            "description": "Consulta o manual oficial de políticas da loja sobre: endereço, horário de funcionamento, garantia legal/fabricante, formas de pagamento, regras de troca e WhatsApp.",
            "parameters": StorePolicySearchInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_return_eligibility",
            "description": "Avalia elegibilidade de troca ou devolução (direito de arrependimento CDC de 7 dias, defeito de fabricação de 30 dias na loja, ou preferência).",
            "parameters": ReturnEligibilityInput.model_json_schema(),
        },
    },
]
