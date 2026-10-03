"""Səhifə tənzimləməsi, CSS stili və başlıq."""
import streamlit as st

import config

CUSTOM_CSS = """
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
</style>
"""


def setup_page() -> None:
    """Səhifə başlığı, enli rejim və ikon. main.py-da ilk Streamlit əmri olmalıdır."""
    st.set_page_config(page_title=config.PAGE_TITLE, layout="wide", page_icon=config.PAGE_ICON)


def render_header() -> None:
    """Xüsusi CSS-i və əsas başlığı göstərir."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(
        "<h1 class='main-title'>🎬 NVideo Copilot — Visual & Audio Video Navigation</h1>",
        unsafe_allow_html=True,
    )
