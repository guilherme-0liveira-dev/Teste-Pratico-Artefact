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
            "endereço" in last_user_msg or "horário" in last_user_msg or "horario" in last_user_msg
        ):
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="call_mock_2",
                        name="search_store_policies",
                        arguments={"query": "horário de funcionamento e endereço da loja"},
                    )
                ],
            )

        return LLMResponse(
            content="Olá! Sou o assistente virtual da Empório da Música. Como posso ajudar com instrumentos musicais hoje?",
            tool_calls=[],
        )
