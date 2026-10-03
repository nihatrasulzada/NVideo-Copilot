"""Session state (yaddaş) idarəetməsi."""
import os

import streamlit as st

DEFAULTS = {
    "groq_api_key": None,      # Sidebar-dakı açar (ilkin dəyər mühitdən götürülür)
    "raw_video_path": None,    # Cari videonun yolu
    "raw_audio_path": None,    # Çıxarılan audionun yolu
    "upload_key": None,        # Son emal olunan yükləmənin kimliyi (təkrar yazmamaq üçün)
    "segments": [],            # İndekslənmiş seqmentlər
    "transcript": None,        # Transkript mətni
    "detected_language": None, # Whisper-in aşkarladığı dil
    "chat_history": [],        # Sual-cavab tarixçəsi
    "last_explanation": None,  # Ekrandakı cavab
    "last_clips": [],          # Ekrandakı klip(lər)
}


def init_state() -> None:
    """Yaddaşda olmayan açarları ilkin dəyərləri ilə yaradır."""
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = list(value) if isinstance(value, list) else value
    if st.session_state["groq_api_key"] is None:
        st.session_state["groq_api_key"] = os.getenv("GROQ_API_KEY", "")


def reset_answer() -> None:
    """Ekrandakı cavabı və klipləri sıfırlayır."""
    st.session_state["last_explanation"] = None
    st.session_state["last_clips"] = []


def reset_conversation() -> None:
    """Tarixçəni və cavabı sıfırlayır."""
    st.session_state["chat_history"] = []
    reset_answer()


def reset_index() -> None:
    """Yeni video seçiləndə köhnə indeksi və söhbəti təmizləyir."""
    st.session_state["segments"] = []
    st.session_state["transcript"] = None
    st.session_state["detected_language"] = None
    reset_conversation()


def add_to_history(query: str, answer: str, clips: list) -> None:
    """Sual-cavabı tarixçəyə yazır və onu aktiv cavab edir."""
    st.session_state["chat_history"].append({"query": query, "answer": answer, "clips": clips})
    st.session_state["last_explanation"] = answer
    st.session_state["last_clips"] = clips
