"""NVideo Copilot — giriş nöqtəsi. İşə salmaq: streamlit run main.py"""
import streamlit as st

from core.state import init_state
from ui.assistant_panel import render_assistant_panel
from ui.header import render_header, setup_page
from ui.sidebar import render_sidebar
from ui.video_panel import render_video_panel


def main() -> None:
    setup_page()  # İlk Streamlit əmri olmalıdır
    render_header()
    init_state()
    render_sidebar()

    col_video, col_assistant = st.columns([1, 1], gap="medium")
    with col_video:
        render_video_panel()
    with col_assistant:
        render_assistant_panel()


if __name__ == "__main__":
    main()
