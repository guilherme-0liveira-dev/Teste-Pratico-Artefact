"""Tests for the out-of-scope question fallback protocol in Empório AI."""

from app.agent.orchestrator import AgentOrchestrator
from app.llm.provider import MockLLMProvider


def test_out_of_scope_accessories_fallback():
    """Verify that asking for accessories triggers the 4-part structured fallback response."""
    provider = MockLLMProvider()
    orchestrator = AgentOrchestrator(provider=provider)

    result = orchestrator.handle_message("Vocês vendem palhetas e encordoamento para violão?")
    response = result.response_text

    # 1. Clear limitation statement
    assert "não comercializa acessórios avulsos" in response or "não pode atender" in response

    # 2. Reason why
    assert "exclusivamente na venda de instrumentos" in response

    # 3. List of what CAN be done at the store
    assert "Catálogo Completo de Instrumentos" in response
    assert "Estoque e Preços" in response
    assert "Condições de Pagamento" in response or "12x sem juros" in response
    assert "Status de Pedidos" in response or "Políticas da Loja" in response

    # 4. Suggestions and human escalation
    assert "(67) 3341-4444" in response


def test_out_of_scope_services_fallback():
    """Verify that asking for services triggers the fallback response."""
    provider = MockLLMProvider()
    orchestrator = AgentOrchestrator(provider=provider)

    result = orchestrator.handle_message("Vocês dão aulas de guitarra ou fazem conserto de luthier?")
    response = result.response_text

    assert "não" in response
    assert "aulas" in response or "luthieria" in response
    assert "Catálogo Completo de Instrumentos" in response
    assert "(67) 3341-4444" in response
