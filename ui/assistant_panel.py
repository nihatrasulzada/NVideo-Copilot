"""Sağ sütun: transkript, sual-cavab və kəsilmiş kliplər."""
import os

import streamlit as st

import config
from core import llm, media, vector_store
from core.formatting import (
    build_context,
    extract_citations,
    format_clock,
    pick_clip_starts,
    to_srt,
)
from core.state import add_to_history


def _safe_search(query: str) -> list[int]:
    try:
        return vector_store.search(query)
    except Exception:
        return []  # Axtarış alınmasa da cavab verməyə davam et


def _clip_candidates(answer: str, segments, hits: list[int]) -> list[int]:
    """Klip vaxtları: əvvəlcə LLM-in istinad etdiyi saniyələr, sonra axtarış nəticələri."""
    max_ts = int(segments[-1].end) + 1 if segments else None
    cited = extract_citations(answer, max_ts=max_ts)
    from_search = [segments[i].timestamp for i in hits if 0 <= i < len(segments)]
    return cited + from_search


def _handle_question(query: str) -> None:
    api_key = st.session_state.get("groq_api_key")
    if not api_key:
        st.error("Please enter your Groq API Key in the left sidebar!")
        return
    if not query:
        st.warning("Please type a question!")
        return

    segments = st.session_state["segments"]
    with st.spinner("Generating response..."):
        try:
            hits = _safe_search(query)
            context = build_context(
                segments, hits, config.CONTEXT_CHAR_LIMIT, config.CONTEXT_NEIGHBORS
            )
            answer = llm.ask(api_key, context, query)

            starts = pick_clip_starts(
                _clip_candidates(answer, segments, hits),
                limit=config.MAX_CLIPS,
                min_gap=config.MIN_CLIP_GAP_SEC,
            )
            video = st.session_state.get("raw_video_path")
            clips = [c for c in (media.cut_clip(video, s) for s in starts) if c]
        except Exception as err:
            st.error(f"Error: {llm.describe_error(err)}")
            return

    add_to_history(query, answer, clips)
    st.rerun()


def _render_transcript() -> None:
    lang = st.session_state.get("detected_language")
    title = "📝 Processed Index Log / Transcript" + (f" (language: {lang})" if lang else "")
    with st.expander(title, expanded=True):
        st.text_area("Transcript", st.session_state["transcript"], height=130, label_visibility="collapsed")
        col_txt, col_srt = st.columns(2)
        col_txt.download_button(
            "⬇️ Download .txt", st.session_state["transcript"],
            file_name="transcript.txt", use_container_width=True,
        )
        col_srt.download_button(
            "⬇️ Download .srt", to_srt(st.session_state["segments"]),
            file_name="transcript.srt", use_container_width=True,
        )


def _render_question_form() -> None:
    with st.form("ask_form"):  # Enter ilə də göndərilir
        query = st.text_input("Ask anything about the video content:", placeholder="Type your query...")
        submitted = st.form_submit_button("🔍 Ask Question", use_container_width=True)
    if submitted:
        _handle_question(query.strip())


def _render_answer() -> None:
    answer = st.session_state.get("last_explanation")
    if answer:
        st.markdown("---")
        st.markdown("### 🤖 NVideo Copilot Response:")
        st.markdown(answer)


def _render_clips() -> None:
    clips = [c for c in st.session_state.get("last_clips", []) if os.path.exists(c.path)]
    if not clips:
        return
    st.markdown("---")
    st.markdown("### ✂️ Extracted Video Clips:")
    tabs = st.tabs([f"▶ {format_clock(c.start)}" for c in clips])
    for tab, clip in zip(tabs, clips):
        with tab:
            st.video(clip.path)
            st.caption(f"📍 Segment cut from second {clip.start} to {clip.end}.")


def render_assistant_panel() -> None:
    st.subheader("2. NVideo Copilot Assistant")

    if st.session_state.get("transcript"):
        _render_transcript()
        _render_question_form()
    else:
        st.info("Upload a video or download a YouTube link, then click 'Process & Analyze Video'.")

    _render_answer()
    _render_clips()
