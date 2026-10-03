import pytest

from core import llm, transcription


def test_get_duration(sample_video):
    assert 5.5 <= transcription.get_duration(sample_video) <= 6.5


def test_describe_video_builds_segments(sample_video, monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "describe_frame", lambda key, jpeg: calls.append(len(jpeg)) or "a test pattern")
    progress = []

    segments = transcription.describe_video(sample_video, "key", on_progress=progress.append)

    assert len(segments) == len(calls) >= 1
    assert all(c > 100 for c in calls)  # Real JPEG baytları göndərilir
    assert segments[0].text == "a test pattern" and segments[0].start == 0
    assert [s.index for s in segments] == list(range(len(segments)))
    assert progress[-1] == pytest.approx(1.0)


def test_describe_video_survives_single_failure(sample_video, monkeypatch):
    state = {"n": 0}

    def flaky(key, jpeg):
        state["n"] += 1
        if state["n"] == 1:
            raise RuntimeError("temporary")
        return "ok"

    monkeypatch.setattr(llm, "describe_frame", flaky)
    segments = transcription.describe_video(sample_video, "key")
    assert segments and all(s.text == "ok" for s in segments)


def test_describe_video_raises_when_everything_fails(sample_video, monkeypatch):
    def always_fail(key, jpeg):
        raise RuntimeError("down")

    monkeypatch.setattr(llm, "describe_frame", always_fail)
    with pytest.raises(RuntimeError, match="down"):
        transcription.describe_video(sample_video, "key")


def test_describe_video_rejects_unreadable_file(tmp_path):
    bad = tmp_path / "bad.mp4"
    bad.write_bytes(b"not a video")
    with pytest.raises(RuntimeError, match="read the video"):
        transcription.describe_video(str(bad), "key")
