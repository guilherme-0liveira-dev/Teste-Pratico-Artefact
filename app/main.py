"""Streamlit web application for Empório AI with a premium Glassmorphism theme."""

import os
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.agent.orchestrator import AgentOrchestrator, AgentTurnResult  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.llm.provider import MockLLMProvider, OpenAICompatibleProvider  # noqa: E402

# Page setup
st.set_page_config(
    page_title="Empório AI — Empório da Música",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# Glassmorphism Design System (CSS)
# ============================================================================

GLASS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Global Font & App Styling */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

h1, h2, h3, h4 {
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.02em;
}

/* Background Ambient Lighting */
.stApp {
    background: radial-gradient(circle at 15% 15%, rgba(67, 56, 202, 0.18) 0%, transparent 40%),
                radial-gradient(circle at 85% 25%, rgba(217, 70, 239, 0.12) 0%, transparent 45%),
                radial-gradient(circle at 50% 80%, rgba(14, 165, 233, 0.10) 0%, transparent 50%),
                #0a0d14 !important;
    background-attachment: fixed !important;
    color: #f1f5f9;
}

/* Glassmorphism Containers */
.glass-card {
    background: rgba(255, 255, 255, 0.035);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.35);
    margin-bottom: 1.25rem;
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: rgba(255, 255, 255, 0.16);
    box-shadow: 0 16px 48px 0 rgba(99, 102, 241, 0.15);
}

.glass-header {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.01) 100%);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 1.75rem 2rem;
    box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.5);
    margin-bottom: 1.5rem;
}

/* Sidebar Glass Effect */
[data-testid="stSidebar"] {
    background: rgba(10, 13, 20, 0.75) !important;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

/* Glass Chat Bubbles */
[data-testid="stChatMessage"] {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 16px !important;
    margin-bottom: 1rem !important;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
}

/* Custom User Bubble */
[data-testid="stChatMessage"]:nth-child(even) {
    border-left: 3px solid #6366f1 !important;
    background: rgba(99, 102, 241, 0.06) !important;
}

/* Custom Assistant Bubble */
[data-testid="stChatMessage"]:nth-child(odd) {
    border-left: 3px solid #a855f7 !important;
}

/* Buttons with Glass Glow */
.stButton > button {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(168, 85, 247, 0.25) 100%) !important;
    backdrop-filter: blur(10px) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 500 !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.2) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    border-color: rgba(255, 255, 255, 0.35) !important;
    box-shadow: 0 8px 24px rgba(168, 85, 247, 0.4) !important;
}

/* Inputs styling */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    color: #f8fafc !important;
}

.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.4) !important;
}

/* Status Chips */
.badge-glass {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 500;
    background: rgba(34, 197, 94, 0.12);
    border: 1px solid rgba(34, 197, 94, 0.3);
    color: #4ade80;
}
.badge-mock {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 500;
    background: rgba(234, 179, 8, 0.12);
    border: 1px solid rgba(234, 179, 8, 0.3);
    color: #facc15;
}
</style>
"""

st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ============================================================================
# Session State Initialization
# ============================================================================


def initialize_session_state() -> None:
    """Initialize conversation history, provider settings, and orchestrator."""
    if "configured_provider" not in st.session_state:
        # Default initialization: check environment variables
        env_key = os.getenv("LLM_API_KEY", settings.LLM_API_KEY)
        has_nvidia_key = bool(env_key and env_key != "your_nvidia_api_key_here")

        if has_nvidia_key:
            st.session_state.provider_type = "nvidia"
            st.session_state.api_key = env_key
            st.session_state.model_name = settings.LLM_MODEL
            st.session_state.base_url = settings.LLM_BASE_URL
            provider = OpenAICompatibleProvider(
                api_key=env_key,
                base_url=settings.LLM_BASE_URL,
                model=settings.LLM_MODEL,
            )
        else:
            # Check if local Ollama might be configured or fallback to mock
            st.session_state.provider_type = "mock"
            st.session_state.api_key = ""
            st.session_state.model_name = "Mock Offline"
            st.session_state.base_url = ""
            provider = MockLLMProvider()

        st.session_state.orchestrator = AgentOrchestrator(provider=provider)
        st.session_state.configured_provider = True

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Olá! 🎶 Seja muito bem-vindo(a) à **Empório da Música**!\n\n"
                    "Sou o **Empório AI**, seu assistente especializado em instrumentos musicais. "
                    "Posso ajudar você a encontrar o instrumento ideal em nosso catálogo, consultar estoque e preços, "
                    "calcular condições de parcelamento sem juros e desconto de 5% no PIX, verificar o status do seu pedido "
                    "ou tirar dúvidas sobre nossas políticas de entrega e garantia.\n\n"
                    "Como posso ajudar a sua música hoje?"
                ),
            }
        ]

    if "last_diagnostics" not in st.session_state:
        st.session_state.last_diagnostics = None


initialize_session_state()


# ============================================================================
# Top Glass Header & First-Access Configuration Card
# ============================================================================

status_badge = (
    f'<span class="badge-glass">🟢 {st.session_state.provider_type.upper()} ({st.session_state.model_name})</span>'
    if st.session_state.provider_type != "mock"
    else '<span class="badge-mock">⚡ MODO DEMONSTRAÇÃO (OFFLINE)</span>'
)

st.markdown(
    f"""
    <div class="glass-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #f8fafc 0%, #cbd5e1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    🎸 Empório AI
                </h1>
                <p style="margin: 0.25rem 0 0 0; color: #94a3b8; font-size: 1.05rem;">
                    Atendimento Inteligente — Empório da Música | Campo Grande - MS
                </p>
            </div>
            <div>
                {status_badge}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# First Access / Quick Model Switcher Glass Card (Collapsible)
with st.expander(
    "⚙️ Configuração do Modelo & Chave de API (NVIDIA NIM / Ollama / Mock)",
    expanded=(st.session_state.provider_type == "mock"),
):
    st.markdown("Configure sua conexão em tempo real sem precisar reiniciar a aplicação:")
    tab_nvidia, tab_ollama, tab_mock = st.tabs(
        ["🚀 NVIDIA NIM (Cloud Free)", "💻 Ollama (Local Privado)", "⚡ Modo Demonstração (Mock)"]
    )

    with tab_nvidia:
        st.caption(
            "Acesse modelos de última geração gratuitamente em [build.nvidia.com](https://build.nvidia.com)."
        )
        col_nv1, col_nv2 = st.columns([2, 1])
        with col_nv1:
            nv_key_input = st.text_input(
                "NVIDIA API Key:",
                value=st.session_state.api_key
                if st.session_state.provider_type == "nvidia"
                else "",
                type="password",
                placeholder="nvapi-...",
                key="input_nv_key",
            )
        with col_nv2:
            nv_model_input = st.text_input(
                "Modelo:",
                value=settings.LLM_MODEL,
                key="input_nv_model",
            )
        if st.button("Conectar NVIDIA NIM", key="btn_connect_nvidia", use_container_width=True):
            if nv_key_input:
                try:
                    new_provider = OpenAICompatibleProvider(
                        api_key=nv_key_input,
                        base_url=settings.LLM_BASE_URL,
                        model=nv_model_input,
                    )
                    st.session_state.orchestrator = AgentOrchestrator(provider=new_provider)
                    st.session_state.provider_type = "nvidia"
                    st.session_state.api_key = nv_key_input
                    st.session_state.model_name = nv_model_input
                    st.session_state.base_url = settings.LLM_BASE_URL
                    st.success("Conectado ao NVIDIA NIM com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao conectar: {e}")
            else:
                st.warning("Por favor, insira a sua NVIDIA API Key.")

    with tab_ollama:
        st.caption("Conecte-se à sua instância local do Ollama rodando no seu computador.")
        col_ol1, col_ol2 = st.columns([2, 1])
        with col_ol1:
            ol_url_input = st.text_input(
                "Endpoint Ollama:",
                value=settings.OLLAMA_BASE_URL,
                key="input_ol_url",
            )
        with col_ol2:
            ol_model_input = st.text_input(
                "Modelo Local:",
                value=settings.OLLAMA_MODEL,
                key="input_ol_model",
            )
        if st.button("Conectar Ollama Local", key="btn_connect_ollama", use_container_width=True):
            try:
                new_provider = OpenAICompatibleProvider(
                    api_key="ollama",
                    base_url=ol_url_input,
                    model=ol_model_input,
                )
                st.session_state.orchestrator = AgentOrchestrator(provider=new_provider)
                st.session_state.provider_type = "ollama"
                st.session_state.api_key = "ollama"
                st.session_state.model_name = ol_model_input
                st.session_state.base_url = ol_url_input
                st.success(f"Conectado ao Ollama local ({ol_model_input})!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao conectar ao Ollama: {e}")

    with tab_mock:
        st.caption(
            "Utilize o simulador determinístico offline com respostas predefinidas para testes rápidos sem consumir rede."
        )
        if st.button("Ativar Modo Mock Offline", key="btn_connect_mock", use_container_width=True):
            st.session_state.orchestrator = AgentOrchestrator(provider=MockLLMProvider())
            st.session_state.provider_type = "mock"
            st.session_state.model_name = "Mock Offline"
            st.info("Modo de teste determinístico ativado.")
            st.rerun()


# ============================================================================
# Sidebar: Information & Technical Diagnostics
# ============================================================================

with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1rem;">
            <img src="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500&auto=format&fit=crop&q=80"
                 style="width: 100%; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 16px rgba(0,0,0,0.4);" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("ℹ️ Dados da Loja")
    st.markdown(
        """
        - 📍 **Endereço:** Rua 14 de Maio, 3200 — Centro, Campo Grande - MS
        - ⏰ **Horário:** Seg a Sex (09h às 18h) | Sáb (09h às 13h)
        - 📱 **WhatsApp:** (67) 3341-4444
        - ✉️ **E-mail:** contato@emporiodamusica.com.br
        """
    )
    st.markdown("---")

    st.subheader("🔍 Diagnóstico Técnico")
    diag: AgentTurnResult | None = st.session_state.last_diagnostics
    if diag:
        st.metric("Latência do Turno", f"{diag.turn_latency_s:.2f}s")
        st.metric("Iterações do Agente", diag.iteration_count)
        st.write(f"**Ferramentas Acionadas ({len(diag.tools_executed)}):**")
        for idx, t in enumerate(diag.tools_executed, 1):
            with st.expander(f"{idx}. `{t.tool_name}` ({t.duration_ms}ms)"):
                st.caption("Argumentos:")
                st.json(t.arguments)
                st.caption("Evidência Retornada:")
                st.code(t.output_snippet, language="text")
    else:
        st.caption("Nenhuma ferramenta acionada ainda nesta sessão.")

    st.markdown("---")
    if st.button("🗑️ Reiniciar Conversa", key="btn_reset_chat", use_container_width=True):
        st.session_state.orchestrator.reset()
        st.session_state.messages = []
        st.session_state.last_diagnostics = None
        st.rerun()


# ============================================================================
# Main Chat Area
# ============================================================================

# Quick Suggestions Chips
st.markdown("##### 💡 Sugestões Rápidas de Consulta:")
c1, c2, c3, c4 = st.columns(4)
prompt_to_send = None

if c1.button("🎸 Violões até R$ 1.000", use_container_width=True):
    prompt_to_send = "Quais opções de violões disponíveis custando até R$ 1.000?"

if c2.button("📍 Endereço e Horário", use_container_width=True):
    prompt_to_send = "Qual o endereço da loja e horário de funcionamento?"

if c3.button("📦 Status do Pedido #8", use_container_width=True):
    prompt_to_send = "Gostaria de saber o status do meu pedido número 8."

if c4.button("🔄 Devolução em 15 dias?", use_container_width=True):
    prompt_to_send = (
        "Me arrependi da compra do meu violão há 15 dias pela internet, posso devolver?"
    )

# Display Conversation History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input Field
user_input = (
    st.chat_input("Escreva sua pergunta sobre instrumentos, estoque ou políticas...")
    or prompt_to_send
)

if user_input:
    # 1. Append and render user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Process turn via Agent Orchestrator
    with st.chat_message("assistant"):
        with st.spinner("Consultando dados e políticas do Empório..."):
            turn_result: AgentTurnResult = st.session_state.orchestrator.handle_message(user_input)
            st.markdown(turn_result.response_text)

        st.session_state.messages.append(
            {"role": "assistant", "content": turn_result.response_text}
        )
        st.session_state.last_diagnostics = turn_result
        st.rerun()
