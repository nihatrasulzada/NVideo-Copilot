"""Sol panel: API açarı və söhbət tarixçəsi."""
import streamlit as st

from core.state import reset_answer

MAX_TITLE_LEN = 30


def _render_api_key() -> None:
    st.sidebar.header("⚙️ Configuration")
    st.sidebar.text_input(
        "Enter Groq API Key:",
        type="password",
        key="groq_api_key",
        help="Or put GROQ_API_KEY in a .env file so you don't have to type it.",
    )


def _render_history() -> None:
    st.sidebar.markdown("---")
    st.sidebar.header("💬 Chat History")

    if st.sidebar.button("➕ New Chat", use_container_width=True):
        reset_answer()
        st.rerun()

    history = st.session_state["chat_history"]
    if not history:
        st.sidebar.caption("No recent conversations.")
        return

    for idx, item in enumerate(reversed(history)):  # Ən son sual yuxarıda
        title = item["query"]
        if len(title) > MAX_TITLE_LEN:
            title = title[:MAX_TITLE_LEN] + "..."
        if st.sidebar.button(f"💬 {title}", key=f"hist_btn_{idx}", use_container_width=True):
            st.session_state["last_explanation"] = item["answer"]
            st.session_state["last_clips"] = item.get("clips", [])
            st.rerun()


def render_sidebar() -> None:
    _render_api_key()
    _render_history()
