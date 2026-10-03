"""Sol sütun: video mənbəyi (fayl / YouTube), emal rejimi və indeksləmə."""
import os

import streamlit as st

import config
from core import llm, media, transcription, vector_store
from core.formatting import build_transcript
from core.state import reset_conversation, reset_index


def _load_new_source(video_path: str, audio_path=None) -> None:
    """Yeni video seçiləndə köhnə nəticələri təmizləyir."""
    st.session_state["raw_video_path"] = video_path
    st.session_state["raw_audio_path"] = audio_path
    reset_index()
    media.clear_clips()


def _render_upload_tab() -> None:
    uploaded = st.file_uploader("Choose a video file", type=config.ALLOWED_VIDEO_TYPES)
    if uploaded is None:
        return
    key = f"{uploaded.name}:{uploaded.size}"
    if key != st.session_state["upload_key"]:  # Yalnız yeni fayl olanda yaz, hər yenilənmədə yox
        media.clear_work_dir()
        _load_new_source(media.save_uploaded_file(uploaded))
        st.session_state["upload_key"] = key
        st.success("Video file uploaded successfully!")


def _render_youtube_tab() -> None:
    url = st.text_input("Paste YouTube Video URL:").strip()
    if url and st.button("Download & Load YouTube Video", use_container_width=True):
        with st.spinner("Downloading YouTube video and extracting audio..."):
            try:
                media.clear_work_dir()
                video_path, audio_path = media.download_youtube(url)
                _load_new_source(video_path, audio_path)
                st.success("YouTube video successfully loaded!")
            except Exception as err:
                st.error(f"YouTube Download Error: {err}")


def _render_advanced_options() -> tuple[str, str | None]:
    """Whisper modeli və dili. (model_ölçüsü, dil_kodu) qaytarır."""
    with st.expander("⚙️ Speech recognition options"):
        model_size = st.selectbox(
            "Whisper model size",
            config.WHISPER_MODEL_SIZES,
            index=config.WHISPER_MODEL_SIZES.index(config.DEFAULT_WHISPER_MODEL),
            help="Bigger = more accurate but slower. 'small' is recommended for Azerbaijani.",
        )
        language_label = st.selectbox("Spoken language", list(config.WHISPER_LANGUAGES))
    return model_size, config.WHISPER_LANGUAGES[language_label]


def _index_audio(video_path: str, model_size: str, language, bar):
    audio = st.session_state.get("raw_audio_path")
    if not audio or not os.path.exists(audio):
        audio = media.extract_wav_from_video(video_path)
    if not audio:
        raise RuntimeError("This video has no audio track. Switch to 'Silent / Visual Frames' mode.")
    return transcription.transcribe_audio(
        audio, model_size, language,
        on_progress=lambda p: bar.progress(p, text=f"Transcribing speech... {int(p * 100)}%"),
    )


def _index_frames(video_path: str, bar):
    api_key = st.session_state["groq_api_key"]
    segments = transcription.describe_video(
        video_path, api_key,
        on_progress=lambda p: bar.progress(p, text=f"Describing video frames... {int(p * 100)}%"),
    )
    return segments, None


def _process_video(video_path: str, mode: str, model_size: str, language) -> None:
    if mode == config.MODE_SILENT and not st.session_state["groq_api_key"]:
        st.error("Visual mode describes frames with Groq. Please enter your Groq API Key in the sidebar.")
        return

    reset_conversation()
    media.clear_clips()
    bar = st.progress(0.0, text="Starting...")
    try:
        if mode == config.MODE_AUDIO:
            segments, language_found = _index_audio(video_path, model_size, language, bar)
        else:
            segments, language_found = _index_frames(video_path, bar)
    except Exception as err:
        st.error(f"Analysis error: {llm.describe_error(err)}")
        return
    finally:
        bar.empty()

    if not segments:
        st.warning(
            "No speech detected. If this is a silent video, "
            "please switch to 'Silent / Visual Frames' mode."
        )
        return

    try:  # Vektor axtarışı bonusdur: alınmasa da tam transkriptlə işləmək olar
        vector_store.reset_collection()
        vector_store.add_segments(segments)
    except Exception as err:
        st.warning(f"Vector search is unavailable ({err}). The full transcript will be used instead.")

    st.session_state["segments"] = segments
    st.session_state["transcript"] = build_transcript(segments)
    st.session_state["detected_language"] = language_found
    st.success("Video indexing complete!")


def render_video_panel() -> None:
    st.subheader("1. Video Source & Processing")

    mode = st.radio("Select Processing Mode:", config.PROCESSING_MODES, index=0)
    model_size, language = _render_advanced_options()
    st.markdown("---")

    tab_upload, tab_youtube = st.tabs(["📁 Upload File", "🔗 YouTube URL"])
    with tab_upload:
        _render_upload_tab()
    with tab_youtube:
        _render_youtube_tab()

    video_path = st.session_state.get("raw_video_path")
    if video_path and os.path.exists(video_path):
        st.video(video_path)
        if st.button("⚡ Process & Analyze Video", use_container_width=True):
            _process_video(video_path, mode, model_size, language)
