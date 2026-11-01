"""Streamlit web application for Empório AI with Adobe Color Palette & Glassmorphism."""

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
# Glassmorphism Design System (Adobe Color Palette: #121212, #D6FF00, #BCBCBC, #FFFFFF)
# ============================================================================

GLASS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Global Font & App Reset */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #F7F7F7;
}

h1, h2, h3, h4, h5 {
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.02em;
    color: #FFFFFF !important;
}

/* Background Ambient Lighting (Dark Onyx #121212 + Cyber Lime #D6FF00 Accents) */
.stApp {
    background: radial-gradient(circle at 10% 10%, rgba(214, 255, 0, 0.07) 0%, transparent 40%),
                radial-gradient(circle at 90% 20%, rgba(188, 188, 188, 0.05) 0%, transparent 45%),
                radial-gradient(circle at 50% 90%, rgba(214, 255, 0, 0.05) 0%, transparent 50%),
                #121212 !important;
    background-attachment: fixed !important;
}

/* Glassmorphism Containers */
.glass-header {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(188, 188, 188, 0.18);
    border-radius: 20px;
    padding: 1.5rem 2rem;
    box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.7);
    margin-bottom: 1.5rem;
}

/* Sidebar Glass Effect */
[data-testid="stSidebar"] {
    background: rgba(18, 18, 18, 0.88) !important;
    backdrop-filter: blur(28px);
    -webkit-backdrop-filter: blur(28px);
    border-right: 1px solid rgba(188, 188, 188, 0.12);
}

/* Glass Chat Bubbles */
[data-testid="stChatMessage"] {
    background: rgba(255, 255, 255, 0.035) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(188, 188, 188, 0.12) !important;
    border-radius: 16px !important;
    margin-bottom: 1rem !important;
    padding: 1rem 1.4rem !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4) !important;
}

/* Custom User Bubble (Neon Lime #D6FF00 Accent Border) */
[data-testid="stChatMessage"]:nth-child(even) {
    border-left: 4px solid #D6FF00 !important;
    background: rgba(214, 255, 0, 0.03) !important;
}

/* Custom Assistant Bubble (Chrome #BCBCBC Accent Border) */
[data-testid="stChatMessage"]:nth-child(odd) {
    border-left: 4px solid #BCBCBC !important;
}

/* Buttons with Neon Cyber Lime Glow */
.stButton > button {
    background: rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(12px) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(188, 188, 188, 0.25) !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 600 !important;
    transition: all 0.25s ease !important;
}

.stButton > button:hover {
    background: #D6FF00 !important;
    color: #121212 !important;
    border-color: #D6FF00 !important;
    box-shadow: 0 0 20px rgba(214, 255, 0, 0.6) !important;
    transform: translateY(-2px);
}

/* Inputs styling */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(188, 188, 188, 0.2) !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
}

.stTextInput > div > div > input:focus {
    border-color: #D6FF00 !important;
    box-shadow: 0 0 16px rgba(214, 255, 0, 0.3) !important;
}

/* Badges */
.badge-lime {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 1rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 700;
    background: rgba(214, 255, 0, 0.12);
    border: 1px solid #D6FF00;
    color: #D6FF00;
    box-shadow: 0 0 14px rgba(214, 255, 0, 0.25);
}

.badge-silver {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 1rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 600;
    background: rgba(188, 188, 188, 0.1);
    border: 1px solid rgba(188, 188, 188, 0.4);
    color: #BCBCBC;
}
</style>
"""

st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ============================================================================
# Session State Initialization
# ============================================================================


def initialize_session_state() -> None:
    """Initialize conversation history, provider settings, and notifications."""
    if "configured_provider" not in st.session_state:
        # Check environment keys
        env_key = os.getenv("LLM_API_KEY", settings.LLM_API_KEY)
        has_nvidia_key = bool(env_key and env_key != "your_nvidia_api_key_here")

        if has_nvidia_key:
            st.session_state.provider_type = "nvidia"
            st.session_state.api_key = env_key
            st.session_state.model_name = settings.LLM_MODEL
            st.session_state.base_url = settings.LLM_BASE_URL
            st.session_state.status_text = f"NVIDIA NIM ({settings.LLM_MODEL})"
            provider = OpenAICompatibleProvider(
                api_key=env_key,
                base_url=settings.LLM_BASE_URL,
                model=settings.LLM_MODEL,
            )
        else:
            # Safe default: Mock offline demo
            st.session_state.provider_type = "mock"
            st.session_state.api_key = ""
            st.session_state.model_name = "Mock Offline"
            st.session_state.base_url = ""
            st.session_state.status_text = "Modo Demonstração Offline"
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
                    "Posso ajudar você a encontrar o instrumento ideal em nosso catálogo, consultar estoque e preços em tempo real, "
                    "calcular condições de parcelamento sem juros e desconto de 5% no PIX, verificar o status do seu pedido "
                    "ou tirar dúvidas sobre nossas políticas de entrega e garantia.\n\n"
                    "Como posso ajudar sua música hoje?"
                ),
            }
        ]

    if "last_diagnostics" not in st.session_state:
        st.session_state.last_diagnostics = None

    if "toast_message" in st.session_state:
        msg, icon = st.session_state.pop("toast_message")
        st.toast(msg, icon=icon)


initialize_session_state()


# ============================================================================
# Glass Header with Status Badge
# ============================================================================

if st.session_state.provider_type == "nvidia":
    badge_html = f'<span class="badge-lime">🟢 {st.session_state.status_text}</span>'
elif st.session_state.provider_type == "ollama":
    badge_html = f'<span class="badge-lime">💻 {st.session_state.status_text}</span>'
else:
    badge_html = '<span class="badge-silver">⚡ MODO DEMONSTRAÇÃO (OFFLINE)</span>'

st.markdown(
    f"""
    <div class="glass-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; color: #FFFFFF;">
                    🎸 Empório AI
                </h1>
                <p style="margin: 0.35rem 0 0 0; color: #BCBCBC; font-size: 1.05rem;">
                    Atendimento Inteligente — <strong style="color: #D6FF00;">Empório da Música</strong> | Campo Grande - MS
                </p>
            </div>
            <div>
                {badge_html}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# First-Access Setup & Connection Testing Glass Card
# ============================================================================

with st.expander(
    "⚙️ Configurar Conexão do Modelo (NVIDIA NIM / Ollama / Mock)",
    expanded=(st.session_state.provider_type == "mock"),
):
    st.markdown("Selecione e teste o provedor de LLM que deseja utilizar:")
    tab_nvidia, tab_ollama, tab_mock = st.tabs(
        [
            "🚀 NVIDIA NIM (Cloud Free)",
            "💻 Ollama (Local Privado)",
            "⚡ Modo Demonstração (Mock Offline)",
        ]
    )

    # 1. NVIDIA NIM TAB
    with tab_nvidia:
        st.caption("Obtenha sua chave gratuita em [build.nvidia.com](https://build.nvidia.com).")
        col_nv1, col_nv2 = st.columns([2, 1])
        with col_nv1:
            nv_key = st.text_input(
                "NVIDIA API Key:",
                value=st.session_state.api_key
                if st.session_state.provider_type == "nvidia"
                else "",
                type="password",
                placeholder="nvapi-...",
                key="nv_key_input",
            )
        with col_nv2:
            nv_model = st.text_input(
                "Modelo:",
                value=settings.LLM_MODEL,
                key="nv_model_input",
            )

        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("Conectar e Testar NVIDIA NIM", key="btn_nv_connect"):
                if not nv_key.strip():
                    st.error("Por favor, insira sua chave NVIDIA API Key (começa com 'nvapi-').")
                else:
                    with st.spinner("Testando conexão com NVIDIA NIM..."):
                        test_provider = OpenAICompatibleProvider(
                            api_key=nv_key.strip(),
                            base_url=settings.LLM_BASE_URL,
                            model=nv_model.strip(),
                        )
                        ok, info = test_provider.verify_connection()
                        if ok:
                            st.session_state.orchestrator = AgentOrchestrator(
                                provider=test_provider
                            )
                            st.session_state.provider_type = "nvidia"
                            st.session_state.api_key = nv_key.strip()
                            st.session_state.model_name = nv_model.strip()
                            st.session_state.base_url = settings.LLM_BASE_URL
                            st.session_state.status_text = f"NVIDIA NIM ({nv_model.strip()})"
                            st.session_state.toast_message = (
                                "NVIDIA NIM conectado e validado!",
                                "🚀",
                            )
                            st.rerun()
                        else:
                            st.error(f"Erro na conexão: {info}")

    # 2. OLLAMA TAB
    with tab_ollama:
        st.caption(
            "Conecte-se a uma instância do Ollama rodando localmente (ex: `ollama run qwen2.5-coder:7b`)."
        )
        col_ol1, col_ol2 = st.columns([2, 1])
        with col_ol1:
            ol_url = st.text_input(
                "Endpoint Ollama:",
                value=settings.OLLAMA_BASE_URL,
                key="ol_url_input",
            )
        with col_ol2:
            ol_model = st.text_input(
                "Modelo Local:",
                value=settings.OLLAMA_MODEL,
                key="ol_model_input",
            )

        if st.button("Conectar e Testar Ollama Local", key="btn_ol_connect"):
            with st.spinner("Testando conexão com Ollama local..."):
                test_provider = OpenAICompatibleProvider(
                    api_key="ollama",
                    base_url=ol_url.strip(),
                    model=ol_model.strip(),
                )
                ok, info = test_provider.verify_connection()
                if ok:
                    st.session_state.orchestrator = AgentOrchestrator(provider=test_provider)
                    st.session_state.provider_type = "ollama"
                    st.session_state.api_key = "ollama"
                    st.session_state.model_name = ol_model.strip()
                    st.session_state.base_url = ol_url.strip()
                    st.session_state.status_text = f"Ollama Local ({ol_model.strip()})"
                    st.session_state.toast_message = (
                        f"Ollama local conectado com sucesso ({ol_model.strip()})!",
                        "💻",
                    )
                    st.rerun()
                else:
                    st.warning(f"{info}\nDica: Verifique se executou `ollama serve` no terminal.")

    # 3. MOCK OFFLINE TAB
    with tab_mock:
        st.caption(
            "Modo de teste determinístico offline com respostas rápidas e execução das ferramentas reais."
        )
        if st.button("Ativar Modo Demonstração Offline", key="btn_mock_connect"):
            st.session_state.orchestrator = AgentOrchestrator(provider=MockLLMProvider())
            st.session_state.provider_type = "mock"
            st.session_state.model_name = "Mock Offline"
            st.session_state.status_text = "Modo Demonstração Offline"
            st.session_state.toast_message = ("Modo Demonstração Offline Ativado!", "⚡")
            st.rerun()


# ============================================================================
# Sidebar: Store Info & Diagnostics
# ============================================================================

with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1rem;">
            <img src="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500&auto=format&fit=crop&q=80"
                 style="width: 100%; border-radius: 12px; border: 1px solid rgba(188,188,188,0.2); box-shadow: 0 4px 16px rgba(0,0,0,0.6);" />
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
    if st.button("🗑️ Reiniciar Conversa", key="btn_reset_chat"):
        st.session_state.orchestrator.reset()
        st.session_state.messages = []
        st.session_state.last_diagnostics = None
        st.session_state.toast_message = ("Histórico de conversa reiniciado!", "🗑️")
        st.rerun()


# ============================================================================
# Main Chat Area
# ============================================================================

# Quick Suggestions Chips
st.markdown("##### 💡 Sugestões Rápidas de Consulta:")
c1, c2, c3, c4 = st.columns(4)
prompt_to_send = None

if c1.button("🎸 Violões até R$ 1.000", key="sugg_1"):
    prompt_to_send = "Quais opções de violões disponíveis custando até R$ 1.000?"

if c2.button("📍 Endereço e Horário", key="sugg_2"):
    prompt_to_send = "Qual o endereço da loja e horário de funcionamento?"

if c3.button("📦 Status do Pedido #8", key="sugg_3"):
    prompt_to_send = "Gostaria de saber o status do meu pedido número 8."

if c4.button("🔄 Devolução em 15 dias?", key="sugg_4"):
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
        with st.spinner("Consultando dados e políticas da Empório da Música..."):
            turn_result: AgentTurnResult = st.session_state.orchestrator.handle_message(user_input)
            st.markdown(turn_result.response_text)

        st.session_state.messages.append(
            {"role": "assistant", "content": turn_result.response_text}
        )
        st.session_state.last_diagnostics = turn_result
        st.rerun()
