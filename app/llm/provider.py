"""LLM Provider abstraction supporting NVIDIA NIM, OpenAI, and Mock providers."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.core.logging import logger


@dataclass
class ToolCallRequest:
    """Standardized tool call request from an LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Standardized response from an LLM provider."""

    content: str | None
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    raw_message: Any | None = None
    finish_reason: str = "stop"


class BaseLLMProvider(ABC):
    """Abstract interface for LLM completion providers."""

    @abstractmethod
    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Execute chat completion with optional structured tool calling."""
        pass

    @abstractmethod
    def verify_connection(self) -> tuple[bool, str]:
        """Verify if provider endpoint is reachable and authenticated."""
        pass


class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI and NVIDIA NIM compatible provider."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = base_url or settings.LLM_BASE_URL
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE

        # Initialize OpenAI client with custom base_url (NVIDIA NIM or Ollama endpoint)
        self.client = OpenAI(
            api_key=self.api_key or "no-key-provided",
            base_url=self.base_url,
            timeout=30.0,
        )

    def verify_connection(self) -> tuple[bool, str]:
        """Test if the endpoint and model are reachable and credentials are valid."""
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=2,
                timeout=6.0,
            )
            return True, f"Conexão ativa com sucesso! Modelo '{self.model}' respondeu."
        except Exception as e:
            err_msg = str(e)
            if (
                "Connection" in err_msg
                or "Failed to connect" in err_msg
                or "11434" in err_msg
                or "refused" in err_msg.lower()
            ):
                return (
                    False,
                    f"Servidor inacessível em {self.base_url}. Verifique se o serviço (ex: Ollama) está rodando.",
                )
            if (
                "Authentication" in err_msg
                or "401" in err_msg
                or "Unauthorized" in err_msg.lower()
                or "invalid api key" in err_msg.lower()
            ):
                return (
                    False,
                    "Chave de API inválida ou ausente. Verifique sua chave no build.nvidia.com.",
                )
            return False, f"Falha na conexão: {err_msg[:140]}"

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message

            tool_calls: list[ToolCallRequest] = []
            if getattr(message, "tool_calls", None):
                for tc in message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}
                    tool_calls.append(
                        ToolCallRequest(
                            id=tc.id,
                            name=tc.function.name,
                            arguments=args,
                        )
                    )

            return LLMResponse(
                content=message.content,
                tool_calls=tool_calls,
                raw_message=message,
                finish_reason=choice.finish_reason or "stop",
            )
        except Exception as e:
            logger.error(f"Error calling LLM provider ({self.base_url}): {e}")
            raise


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for offline tests and continuous integration."""

    def __init__(self, predefined_responses: list[LLMResponse] | None = None):
        self.responses = predefined_responses or []
        self.call_history: list[list[dict[str, Any]]] = []

    def set_responses(self, responses: list[LLMResponse]) -> None:
        self.responses = responses

    def verify_connection(self) -> tuple[bool, str]:
        """Mock provider is always available offline."""
        return True, "Modo Demonstração Offline ativo (Simulador determinístico)."

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        self.call_history.append(messages)
        if self.responses:
            return self.responses.pop(0)

        # Check if the previous message was a tool result: synthesize answer
        if messages and messages[-1].get("role") == "tool":
            last_tool_msg = messages[-1].get("content", "")
            # Find the tool that was called
            tool_name = ""
            for m in reversed(messages[:-1]):
                if m.get("tool_calls"):
                    tool_name = m["tool_calls"][0].name
                    break

            if tool_name == "search_products":
                return LLMResponse(
                    content=(
                        "Consultando nosso catálogo em tempo real, temos excelentes opções de violões disponíveis até R$ 1.000,00:\n\n"
                        "🟢 **Mais Acessíveis:**\n"
                        "- 🎸 **Tagima Memphis AC-39 (Nylon)** — R$ 429,90\n"
                        "  - À vista no PIX (5% off): **R$ 408,40**\n"
                        "  - Cartão: até **3x de R$ 143,30** sem juros\n\n"
                        "- 🎸 **Rozini RC-104 (Nylon)** — R$ 459,90\n"
                        "  - À vista no PIX (5% off): **R$ 436,90**\n"
                        "  - Cartão: até **3x de R$ 153,30** sem juros\n\n"
                        "🟡 **Intermediários:**\n"
                        "- 🎸 **Yamaha C40 (Nylon)** — R$ 599,90\n"
                        "  - À vista no PIX (5% off): **R$ 569,90**\n"
                        "  - Cartão: até **6x de R$ 99,98** sem juros (parcela mínima de R$ 80,00)\n\n"
                        "- 🎸 **Yamaha F310 (Aço)** — R$ 699,90\n"
                        "  - À vista no PIX (5% off): **R$ 664,90**\n"
                        "  - Cartão: até **6x de R$ 116,65** sem juros (parcela mínima de R$ 80,00)\n\n"
                        "🔵 **Mais Robustos (até o limite de R$ 1.000):**\n"
                        "- 🎸 **Shelby SGD-195E (Elétrico Aço)** — R$ 799,00\n"
                        "  - À vista no PIX (5% off): **R$ 759,05**\n"
                        "  - Cartão: até **7x de R$ 114,14** sem juros (parcela mínima de R$ 100,00)\n\n"
                        "- 🎸 **Yamaha C70 (Nylon)** — R$ 849,00\n"
                        "  - À vista no PIX (5% off): **R$ 806,55**\n"
                        "  - Cartão: até **8x de R$ 106,12** sem juros (parcela mínima de R$ 100,00)\n\n"
                        "🚚 **Frete:** Grátis em Campo Grande para compras a partir de R$ 500,00 (1 a 3 dias úteis). "
                        "Todos os modelos contam com 90 dias de garantia legal. Gostaria de reservar algum desses modelos?"
                    ),
                    tool_calls=[],
                )
            elif tool_name == "get_order_status":
                return LLMResponse(
                    content=(
                        "Localizei o seu pedido em nossa base de dados:\n\n"
                        "📦 **Pedido #8**\n"
                        "- **Status:** Entregue ao cliente\n"
                        "- **Data da Entrega:** 18/01/2025\n\n"
                        "ℹ️ **Prazo de Devolução (CDC):**\n"
                        "Conforme o Artigo 49 do Código de Defesa do Consumidor, compras realizadas pela internet "
                        "possuem **7 dias corridos** após o recebimento para devolução por arrependimento com reembolso integral.\n\n"
                        "Posso ajudar com mais algum detalhe sobre seu pedido?"
                    ),
                    tool_calls=[],
                )
            elif tool_name == "search_store_policies":
                return LLMResponse(
                    content=(
                        "Aqui estão as diretrizes oficiais da **Empório da Música**:\n\n"
                        "💳 **Formas de Pagamento e Desconto PIX:**\n"
                        "- **PIX à vista:** 5% de desconto automático sobre o preço regular (não cumulativo com promoções ativas).\n"
                        "- **Cartão de Crédito sem juros:**\n"
                        "  - 1x a 3x: sem valor mínimo por parcela\n"
                        "  - 4x a 6x: parcela mínima de R$ 80,00\n"
                        "  - 7x a 12x: parcela mínima de R$ 100,00\n\n"
                        "🚚 **Entrega em Campo Grande - MS:**\n"
                        "- Frete Grátis em compras a partir de R$ 500,00 (entrega de 1 a 3 dias úteis via motoboy).\n"
                        "- Taxa fixa de R$ 35,00 para pedidos abaixo de R$ 500,00.\n\n"
                        "Deseja calcular as condições para um instrumento específico?"
                    ),
                    tool_calls=[],
                )
            elif tool_name in ("get_product_details", "check_stock"):
                return LLMResponse(
                    content=(
                        "🎸 **Fender Stratocaster Player Series:**\n\n"
                        "- **Preço Regular:** R$ 7.490,00\n"
                        "- **Disponibilidade:** Em estoque na loja de Campo Grande (3 unidades)\n"
                        "- **Pagamento no PIX (5% off):** **R$ 7.115,50**\n"
                        "- **Parcelamento sem juros:** até **12x de R$ 624,17** no cartão de crédito\n"
                        "- **Frete:** Grátis para Campo Grande (compra acima de R$ 500,00)\n\n"
                        "Deseja que nossa equipe separe este instrumento para você testar em nossa loja?"
                    ),
                    tool_calls=[],
                )

            return LLMResponse(
                content=f"Consultei os registros da loja:\n\n{last_tool_msg[:300]}\n\nComo posso prosseguir?",
                tool_calls=[],
            )

        # Smart default heuristic for mock tests
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = str(m.get("content", "")).lower()
                break

        if "viol" in last_user_msg or "violão" in last_user_msg:
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="call_mock_1",
                        name="search_products",
                        arguments={"category": "Violões", "max_price": 1000.0},
                    )
                ],
            )
        elif (
            "endereço" in last_user_msg
            or "horário" in last_user_msg
            or "horario" in last_user_msg
            or "pix" in last_user_msg
            or "parcel" in last_user_msg
            or "política" in last_user_msg
            or "politica" in last_user_msg
        ):
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="call_mock_2",
                        name="search_store_policies",
                        arguments={"query": "pagamento parcelamento pix políticas da loja"},
                    )
                ],
            )
        elif "pedido" in last_user_msg or "#8" in last_user_msg:
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="call_mock_3",
                        name="get_order_status",
                        arguments={"order_id": 8},
                    )
                ],
            )
        elif "fender" in last_user_msg or "stratocaster" in last_user_msg:
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="call_mock_4",
                        name="get_product_details",
                        arguments={"product_name": "Fender Player Stratocaster"},
                    )
                ],
            )

        return LLMResponse(
            content="Olá! Sou o assistente virtual da Empório da Música. Como posso ajudar com instrumentos musicais hoje?",
            tool_calls=[],
        )
