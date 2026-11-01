"""Streamlit web application for Empório AI — Intelligent Customer Service Agent."""

import os
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.agent.orchestrator import AgentOrchestrator, AgentTurnResult
from app.core.config import settings
from app.llm.provider import MockLLMProvider, OpenAICompatibleProvider

# Streamlit Page Configuration
st.set_page_config(
    page_title="Empório AI — Empório da Música",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state() -> None:
    """Initialize conversation history and orchestrator in session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Olá! 🎶 Seja muito bem-vindo(a) à **Empório da Música**!\n\n"
                    "Sou o **Empório AI**, seu assistente especializado em instrumentos musicais. "
                    "Posso ajudar você a encontrar o instrumento ideal no nosso catálogo, verificar estoque e preços, "
                    "calcular condições de parcelamento e desconto no PIX, consultar o status do seu pedido ou tirar dúvidas "
                    "sobre nossas políticas de entrega e garantia.\n\n"
                    "Como posso ajudar sua música hoje?"
                ),
            }
        ]

    if "last_diagnostics" not in st.session_state:
        st.session_state.last_diagnostics = None

    if "orchestrator" not in st.session_state:
        # Determine provider: if API key is set in env or sidebar, use OpenAICompatibleProvider
        api_key = os.getenv("LLM_API_KEY", settings.LLM_API_KEY)
        if api_key and api_key != "your_nvidia_api_key_here":
            provider = OpenAICompatibleProvider(api_key=api_key)
        else:
            # Fallback to smart MockLLMProvider for offline presentation
            provider = MockLLMProvider()

        st.session_state.orchestrator = AgentOrchestrator(provider=provider)


initialize_session_state()


# ============================================================================
# Sidebar: Store Info, Settings & Diagnostics
# ============================================================================

with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500&auto=format&fit=crop&q=80",
        caption="Empório da Música — Campo Grande / MS",
        use_container_width=True,
    )
    st.title("🎸 Empório da Música")
    st.caption("Sua música começa aqui.")
    st.markdown("---")

    st.subheader("ℹ️ Informações da Loja")
    st.markdown(
        """
        - **Endereço:** Rua 14 de Maio, 3200 — Centro, Campo Grande - MS
        - **Horário:** Seg a Sex (09h às 18h) | Sáb (09h às 13h)
        - **WhatsApp:** (67) 3341-4444
        - **E-mail:** contato@emporiodamusica.com.br
        """
    )
    st.markdown("---")

    st.subheader("⚙️ Configurações do Modelo")
    provider_mode = st.radio(
        "Selecione o Provedor:",
        ["NVIDIA NIM (Cloud Free)", "Ollama (Local)", "Modo Demonstração (Mock Offline)"],
        index=0
        if settings.LLM_PROVIDER == "nvidia"
        else (1 if settings.LLM_PROVIDER == "ollama" else 2),
    )

    if provider_mode == "NVIDIA NIM (Cloud Free)":
        nvidia_key = st.text_input(
            "NVIDIA API Key:",
            value=settings.LLM_API_KEY
            if settings.LLM_API_KEY != "your_nvidia_api_key_here"
            else "",
            type="password",
            help="Obtenha sua chave gratuita em https://build.nvidia.com",
        )
        nvidia_model = st.text_input("Modelo:", value=settings.LLM_MODEL)
        nvidia_base_url = st.text_input("Base URL:", value=settings.LLM_BASE_URL)

        if st.button("Conectar NVIDIA NIM", use_container_width=True):
            if nvidia_key:
                provider = OpenAICompatibleProvider(
                    api_key=nvidia_key,
                    base_url=nvidia_base_url,
                    model=nvidia_model,
                )
                st.session_state.orchestrator = AgentOrchestrator(provider=provider)
                st.success(f"NVIDIA NIM conectado ({nvidia_model})!")
            else:
                st.warning("Por favor, insira sua NVIDIA API Key.")

    elif provider_mode == "Ollama (Local)":
        ollama_url = st.text_input(
            "Ollama Endpoint:", value=os.getenv("OPENAI_BASE_URL", settings.OLLAMA_BASE_URL)
        )
        ollama_model = st.text_input(
            "Modelo Local:", value=os.getenv("OPENAI_MODEL", settings.OLLAMA_MODEL)
        )

        if st.button("Conectar Ollama Local", use_container_width=True):
            provider = OpenAICompatibleProvider(
                api_key="ollama",
                base_url=ollama_url,
                model=ollama_model,
            )
            st.session_state.orchestrator = AgentOrchestrator(provider=provider)
            st.success(f"Ollama local conectado ({ollama_model})!")

    else:
        st.caption("Modo de teste determinístico offline com respostas simuladas.")
        if st.button("Ativar Modo Demonstração", use_container_width=True):
            st.session_state.orchestrator = AgentOrchestrator(provider=MockLLMProvider())
            st.info("Modo demonstração ativo.")

    if st.button("🗑️ Reiniciar Conversa", use_container_width=True):
        st.session_state.orchestrator.reset()
        st.session_state.messages = []
        st.session_state.last_diagnostics = None
        st.rerun()

    st.markdown("---")
    st.subheader("🔍 Diagnóstico Técnico")
    diag: AgentTurnResult | None = st.session_state.last_diagnostics
    if diag:
        st.metric("Latência do Turno", f"{diag.turn_latency_s:.2f}s")
        st.metric("Iterações do Agente", diag.iteration_count)
        st.write(f"**Ferramentas Executadas ({len(diag.tools_executed)}):**")
        for idx, t in enumerate(diag.tools_executed, 1):
            with st.expander(f"{idx}. `{t.tool_name}` ({t.duration_ms}ms)"):
                st.json(t.arguments)
                st.code(t.output_snippet, language="text")
    else:
        st.caption("Nenhuma ferramenta acionada ainda.")


# ============================================================================
# Main Chat Area
# ============================================================================

st.markdown("### 🎶 Atendimento Virtual Inteligente")
st.markdown(
    "Tire dúvidas sobre violões, guitarras, teclados, formas de pagamento com PIX ou parcelamento, "
    "consulte pedidos ou saiba tudo sobre nossas políticas de devolução e garantia."
)

# Quick Suggestion Buttons
col1, col2, col3, col4 = st.columns(4)
prompt_to_send = None

if col1.button("🎸 Violões até R$ 1.000", use_container_width=True):
    prompt_to_send = "Quais opções de violões disponíveis custando até R$ 1.000?"

if col2.button("📍 Endereço e Horário", use_container_width=True):
    prompt_to_send = "Qual o endereço da loja e horário de funcionamento?"

if col3.button("📦 Status do Pedido #8", use_container_width=True):
    prompt_to_send = "Gostaria de saber o status do meu pedido número 8."

if col4.button("🔄 Devolução em 15 dias?", use_container_width=True):
    prompt_to_send = (
        "Me arrependi da compra do meu violão há 15 dias pela internet, posso devolver?"
    )

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input from user
user_input = st.chat_input("Escreva sua mensagem aqui...") or prompt_to_send

if user_input:
    # Append and display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process via Orchestrator
    with st.chat_message("assistant"):
        with st.spinner("Consultando catálogo e políticas da loja..."):
            turn_result: AgentTurnResult = st.session_state.orchestrator.handle_message(user_input)
            st.markdown(turn_result.response_text)

        st.session_state.messages.append(
            {"role": "assistant", "content": turn_result.response_text}
        )
        st.session_state.last_diagnostics = turn_result
        st.rerun()
