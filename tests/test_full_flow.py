"""Tam axın: video -> indeksləmə -> sual -> cavab + klip (Groq çağırışları saxta)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from core import llm, vector_store

MAIN = str(Path(__file__).resolve().parent.parent / "main.py")
VISUAL = "🔕 Silent / Visual Frames (Frame Extraction)"


def test_visual_mode_end_to_end(data_dirs, sample_video, monkeypatch):
    monkeypatch.setattr(llm, "describe_frame", lambda key, jpeg: "a colorful test pattern")
    monkeypatch.setattr(llm, "ask", lambda key, ctx, q: f"Answer from context. [3s] and [4s] and [500s]")

    at = AppTest.from_file(MAIN, default_timeout=60)
    at.session_state["raw_video_path"] = sample_video
    at.session_state["groq_api_key"] = "fake-key"
    at.run()
    at.radio[0].set_value(VISUAL).run()
    next(b for b in at.button if "Process" in b.label).click().run()

    assert not at.exception, at.exception
    assert any("indexing complete" in s.value for s in at.success)
    assert at.session_state["segments"]
    assert "[0s]: a colorful test pattern" in at.session_state["transcript"]

    # Sual ver
    next(t for t in at.text_input if "Ask anything" in t.label).set_value("what is shown?")  # forma daxilində: ayrıca run() yoxdur
    next(b for b in at.button if "Ask" in b.label).click().run()

    assert not at.exception, at.exception
    assert not at.error, [e.value for e in at.error]
    assert any("Answer from context" in m.value for m in at.markdown)
    clips = at.session_state["last_clips"]
    assert clips, "klip kəsilməyib"
    assert all(Path(c.path).exists() for c in clips)
    assert at.session_state["chat_history"][0]["query"] == "what is shown?"
