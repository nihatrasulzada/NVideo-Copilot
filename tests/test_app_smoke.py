from pathlib import Path

from streamlit.testing.v1 import AppTest

MAIN = str(Path(__file__).resolve().parent.parent / "main.py")


def test_app_starts_without_errors():
    at = AppTest.from_file(MAIN, default_timeout=30).run()
    assert not at.exception
    subheaders = [s.value for s in at.subheader]
    assert "1. Video Source & Processing" in subheaders
    assert "2. NVideo Copilot Assistant" in subheaders
    assert any("Upload a video" in i.value for i in at.info)


def test_visual_mode_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    video = tmp_path / "v.mp4"
    video.write_bytes(b"x")

    at = AppTest.from_file(MAIN, default_timeout=30)
    at.session_state["raw_video_path"] = str(video)
    at.run()
    at.radio[0].set_value("🔕 Silent / Visual Frames (Frame Extraction)").run()
    process = next(b for b in at.button if "Process" in b.label)
    process.click().run()

    assert any("Groq API Key" in e.value for e in at.error)


def test_answer_and_clips_render_from_state(tmp_path):
    from core.models import Clip, Segment

    clip_file = tmp_path / "c.mp4"
    clip_file.write_bytes(b"x")

    at = AppTest.from_file(MAIN, default_timeout=30)
    at.session_state["segments"] = [Segment(0, 0, 5, "hi")]
    at.session_state["transcript"] = "[0s]: hi"
    at.session_state["last_explanation"] = "Some answer [0s]"
    at.session_state["last_clips"] = [Clip(str(clip_file), 0, 12)]
    at.run()

    assert not at.exception
    assert any("Some answer" in m.value for m in at.markdown)
    assert any("Extracted Video Clips" in m.value for m in at.markdown)
