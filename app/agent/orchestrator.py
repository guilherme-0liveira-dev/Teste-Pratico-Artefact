import re
import time
from dataclasses import dataclass, field
from typing import Any

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import TOOL_REGISTRY, TOOL_SCHEMAS
from app.core.config import settings
from app.core.logging import logger
from app.llm.provider import BaseLLMProvider, MockLLMProvider, OpenAICompatibleProvider


@dataclass
class ToolExecutionLog:
    """Log entry for an executed tool."""

    tool_name: str
    arguments: dict[str, Any]
    output_snippet: str
    duration_ms: float


@dataclass
class AgentTurnResult:
    """Result of an agent conversation turn."""

    response_text: str
    tools_executed: list[ToolExecutionLog] = field(default_factory=list)
    turn_latency_s: float = 0.0
    iteration_count: int = 0


class AgentOrchestrator:
    """Orchestrates conversations, tool dispatches, and LLM reasoning loops."""

    def __init__(self, provider: BaseLLMProvider | None = None):
        self.provider = provider or OpenAICompatibleProvider()
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def reset(self) -> None:
        """Reset conversation history back to initial system prompt."""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def handle_message(self, user_text: str) -> AgentTurnResult:
        """Process a user message through the bounded tool-calling loop."""
        start_time = time.time()
        self.messages.append({"role": "user", "content": user_text})

        tools_log: list[ToolExecutionLog] = []
        iterations = 0
        final_answer = ""

        while iterations < settings.AGENT_MAX_ITERATIONS:
            iterations += 1
            logger.info(f"Agent iteration {iterations}/{settings.AGENT_MAX_ITERATIONS}")

            try:
                llm_response = self.provider.chat_completion(
                    messages=self.messages,
                    tools=TOOL_SCHEMAS,
                )
            except Exception as e:
                logger.error(f"LLM generation failed after retries: {e}")
                # Seamless fallback: if primary provider is OpenAICompatibleProvider (cloud),
                # use deterministic local synthesis so the customer NEVER leaves without an answer!
                if isinstance(self.provider, OpenAICompatibleProvider):
                    try:
                        logger.info(
                            "Engaging seamless local fallback synthesizer to fulfill customer turn..."
                        )
                        fallback_provider = MockLLMProvider()
                        fallback_resp = fallback_provider.chat_completion(self.messages)
                        if fallback_resp.content:
                            final_answer = sanitize_response_text(fallback_resp.content)
                            self.messages.append({"role": "assistant", "content": final_answer})
                            break
                    except Exception as fallback_err:
                        logger.error(f"Fallback synthesis error: {fallback_err}")

                final_answer = (
                    "Desculpe, tive uma instabilidade temporária ao consultar meu sistema. "
                    "Por favor, tente novamente ou entre em contato com nossa equipe no WhatsApp (67) 3341-4444."
                )
                self.messages.append({"role": "assistant", "content": final_answer})
                break

            # Check if LLM requested any tool execution
            if llm_response.tool_calls:
                logger.info(f"LLM requested {len(llm_response.tool_calls)} tool calls.")

                # Construct assistant message with tool calls for history
                assistant_msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": llm_response.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json_dumps(tc.arguments),
                            },
                        }
                        for tc in llm_response.tool_calls
                    ],
                }
                self.messages.append(assistant_msg)

                # Execute requested tools
                for tc in llm_response.tool_calls:
                    tool_fn = TOOL_REGISTRY.get(tc.name)
                    tool_start = time.time()

                    if tool_fn:
                        try:
                            tool_result = tool_fn(tc.arguments)
                        except Exception as ex:
                            logger.error(f"Error executing tool '{tc.name}': {ex}")
                            tool_result = f"Erro na execução da ferramenta {tc.name}: {ex}"
                    else:
                        tool_result = f"Ferramenta '{tc.name}' não reconhecida pelo sistema."

                    tool_duration = (time.time() - tool_start) * 1000
                    snippet = tool_result[:150].replace("\n", " ") + (
                        "..." if len(tool_result) > 150 else ""
                    )
                    tools_log.append(
                        ToolExecutionLog(
                            tool_name=tc.name,
                            arguments=tc.arguments,
                            output_snippet=snippet,
                            duration_ms=round(tool_duration, 2),
                        )
                    )

                    # Append tool response message
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.name,
                            "content": tool_result,
                        }
                    )

                # Continue loop to allow LLM to interpret tool output
                continue

            # If no tool calls, this is the final response
            raw_answer = (
                llm_response.content or "Como posso ajudar você com nossos instrumentos musicais?"
            )
            final_answer = sanitize_response_text(raw_answer)
            self.messages.append({"role": "assistant", "content": final_answer})
            break

        if not final_answer:
            final_answer = (
                "Consultei os dados necessários, mas atingi o limite de processamento para esta dúvida. "
                "Para detalhes adicionais, nossa equipe humana no WhatsApp (67) 3341-4444 está pronta para ajudar!"
            )
            self.messages.append({"role": "assistant", "content": final_answer})
        else:
            final_answer = sanitize_response_text(final_answer)

        total_latency = time.time() - start_time
        return AgentTurnResult(
            response_text=final_answer,
            tools_executed=tools_log,
            turn_latency_s=round(total_latency, 2),
            iteration_count=iterations,
        )


def sanitize_response_text(text: str) -> str:
    """Post-processing guardrail enforcing strict Brazilian currency formatting and preventing leaks.

    - Replaces 'R 429,90' or 'R 500,00' with 'R$ 429,90' or 'R$ 500,00'.
    - Standardizes 'R$429,90' and 'R$   429,90' to 'R$ 429,90'.
    - Strips internal database IDs like '(ID 81)', '(ID: 82)', or '[ID 10]'.
    """
    if not text:
        return text

    # 1. Fix missing $ in currency: 'R 429,90' or 'R 500' -> 'R$ 429,90'
    text = re.sub(r"\bR\s+(?=\d)", "R$ ", text)

    # 2. Fix missing space after R$: 'R$429,90' -> 'R$ 429,90'
    text = re.sub(r"\bR\$(?=\d)", "R$ ", text)

    # 3. Fix multiple spaces after R$: 'R$   429,90' -> 'R$ 429,90'
    text = re.sub(r"\bR\$\s{2,}(?=\d)", "R$ ", text)

    # 4. Remove internal database product IDs if any leaked (e.g. '(ID 81)', '(ID: 82)', '[ID 10]')
    text = re.sub(r"\s*[\(\[]\s*ID:?\s*\d+\s*[\)\]]", "", text, flags=re.IGNORECASE)

    return text


def json_dumps(obj: Any) -> str:
    """Helper to serialize dict to JSON string."""
    import json

    return json.dumps(obj, ensure_ascii=False)
