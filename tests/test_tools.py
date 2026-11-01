"""Integration tests for agent tool executions against SQLite database."""

from app.agent.tools import (
    execute_calculate_pricing_and_installments,
    execute_calculate_shipping_estimate,
    execute_check_stock,
    execute_get_active_promotions,
    execute_get_order_status,
    execute_get_product_details,
    execute_search_products,
    execute_search_store_policies,
)


def test_tool_search_products_guitars():
    """Verify search_products tool returns violões/guitarras matching max_price."""
    result = execute_search_products(
        {"category": "Violões", "max_price": 1000.0, "in_stock_only": True}
    )
    assert "Encontrados" in result
    assert "Violões" in result
    # Check that returned products are under R$ 1000
    assert "Yamaha C40" in result or "Tagima" in result


def test_tool_get_product_details_existing():
    """Verify get_product_details returns complete specs and PIX calculation."""
    result = execute_get_product_details({"product_id_or_name": "Yamaha C40"})
    assert "Yamaha C40" in result
    assert "Valor no PIX" in result
    assert "Condições no Cartão" in result


def test_tool_get_product_details_nonexistent():
    """Verify get_product_details handles unknown products gracefully."""
    result = execute_get_product_details({"product_id_or_name": "Instrumento Inexistente 999"})
    assert "não encontrado" in result.lower()


def test_tool_check_stock():
    """Verify check_stock reports exact availability."""
    result = execute_check_stock({"product_id_or_name": "81"})
    assert "DISPONÍVEL" in result
    assert "unidade(s) em estoque" in result


def test_tool_get_order_status_success():
    """Verify get_order_status retrieves order details."""
    result = execute_get_order_status({"order_id": 1})
    assert "Pedido #1" in result
    assert "Lucas Mendes" in result or "Pedro Henrique" in result
    assert "Status Atual" in result


def test_tool_get_order_status_nonexistent():
    """Verify get_order_status handles missing order gracefully."""
    result = execute_get_order_status({"order_id": 99999})
    assert "não foi encontrado" in result


def test_tool_get_active_promotions():
    """Verify get_active_promotions returns campaigns with active products."""
    result = execute_get_active_promotions({})
    assert "Promoções Ativas" in result
    assert "OFF" in result
    assert "não são cumulativos com o desconto de 5% do PIX" in result


def test_tool_calculate_pricing_and_installments():
    """Verify installment options and non-cumulative PIX logic are clearly broken down."""
    result = execute_calculate_pricing_and_installments({"product_id_or_name": "81"})
    assert "Simulação de Pagamento" in result
    assert "Pagamento via PIX" in result
    assert "sem juros" in result


def test_tool_calculate_shipping_estimate():
    """Verify shipping estimate tool outputs local and external freight rules."""
    local_free = execute_calculate_shipping_estimate(
        {"order_total": 600.0, "destination_city": "Campo Grande"}
    )
    assert "FRETE GRÁTIS" in local_free

    local_fee = execute_calculate_shipping_estimate(
        {"order_total": 400.0, "destination_city": "Campo Grande"}
    )
    assert "R$ 35.00" in local_fee

    external = execute_calculate_shipping_estimate(
        {"order_total": 800.0, "destination_city": "Cuiabá"}
    )
    assert "PAC" in external or "Jadlog" in external


def test_tool_search_store_policies():
    """Verify policy retrieval returns authentic manual citations."""
    hours_res = execute_search_store_policies({"query": "horario de funcionamento da loja"})
    assert "Horário" in hours_res or "Atendimento" in hours_res

    withdrawal_res = execute_search_store_policies(
        {"query": "arrependimento devolução compras online 7 dias"}
    )
    assert "Arrependimento" in withdrawal_res or "Devoluções" in withdrawal_res
