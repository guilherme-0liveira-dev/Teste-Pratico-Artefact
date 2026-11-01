"""Tests for AgentOrchestrator using deterministic MockLLMProvider."""

from app.agent.orchestrator import AgentOrchestrator
from app.llm.provider import LLMResponse, MockLLMProvider, ToolCallRequest


def test_orchestrator_simple_conversation():
    """Verify single-turn response without tool calls."""
    mock = MockLLMProvider(
        predefined_responses=[
            LLMResponse(content="Olá! Como posso ajudar você na Empório da Música?", tool_calls=[])
        ]
    )
    orchestrator = AgentOrchestrator(provider=mock)
    result = orchestrator.handle_message("Olá, boa tarde!")

    assert "Empório da Música" in result.response_text
    assert len(result.tools_executed) == 0
    assert result.iteration_count == 1


def test_orchestrator_tool_calling_loop():
    """Verify multi-step tool call execution and final response synthesis."""
    # Step 1: LLM decides to search for products
    step1_resp = LLMResponse(
        content=None,
        tool_calls=[
            ToolCallRequest(
                id="call_test_1",
                name="search_products",
                arguments={"category": "Violões", "max_price": 1000.0},
            )
        ],
    )
    # Step 2: LLM receives tool output and writes final response
    step2_resp = LLMResponse(
        content="Encontrei ótimas opções de violões até R$ 1.000, como o Yamaha C40 por R$ 599,90 e o Tagima por R$ 429,90!",
        tool_calls=[],
    )

    mock = MockLLMProvider(predefined_responses=[step1_resp, step2_resp])
    orchestrator = AgentOrchestrator(provider=mock)

    result = orchestrator.handle_message("Quais violões até R$ 1.000 vocês têm?")
    assert len(result.tools_executed) == 1
    assert result.tools_executed[0].tool_name == "search_products"
    assert "Yamaha C40" in result.response_text
    assert result.iteration_count == 2


def test_orchestrator_iteration_limit_safeguard():
    """Ensure infinite tool calling loop is bounded by settings.AGENT_MAX_ITERATIONS."""
    # Endless tool calls
    infinite_calls = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id=f"call_{i}",
                    name="search_products",
                    arguments={"query": "loop"},
                )
            ],
        )
        for i in range(10)
    ]

    mock = MockLLMProvider(predefined_responses=infinite_calls)
    orchestrator = AgentOrchestrator(provider=mock)

    result = orchestrator.handle_message("Test loop")
    assert result.iteration_count == 5  # Max iterations limit
    assert "WhatsApp" in result.response_text


def test_orchestrator_provider_failure_graceful_handling():
    """Ensure orchestrator handles unexpected LLM failures without crashing."""

    class FailingProvider(MockLLMProvider):
        def chat_completion(self, messages, tools=None):
            raise ConnectionError("NVIDIA NIM API temporarily unreachable")

    orchestrator = AgentOrchestrator(provider=FailingProvider())
    result = orchestrator.handle_message("Qual o endereço da loja?")
    assert "instabilidade temporária" in result.response_text
    assert "WhatsApp" in result.response_text


def test_orchestrator_reset():
    """Verify reset clears conversation history back to initial system prompt."""
    mock = MockLLMProvider()
    orchestrator = AgentOrchestrator(provider=mock)
    orchestrator.handle_message("Primeira mensagem")
    assert len(orchestrator.messages) > 1

    orchestrator.reset()
    assert len(orchestrator.messages) == 1
    assert orchestrator.messages[0]["role"] == "system"
