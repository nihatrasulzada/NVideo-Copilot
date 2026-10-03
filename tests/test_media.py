from pathlib import Path

from core import media


def test_extract_wav_from_video(data_dirs, sample_video):
    wav = media.extract_wav_from_video(sample_video)
    assert wav is not None and Path(wav).exists()
    assert Path(wav).stat().st_size > 1000


def test_extract_wav_returns_none_without_audio_track(data_dirs, silent_video):
    assert media.extract_wav_from_video(silent_video) is None


def test_cut_clip_creates_playable_file_with_unique_names(data_dirs, sample_video):
    first = media.cut_clip(sample_video, 3)
    second = media.cut_clip(sample_video, 3)
    assert first and second
    assert Path(first.path).exists() and Path(second.path).exists()
    assert first.path != second.path  # Köhnə klip üzərinə yazılmır
    assert (first.start, first.end) == (2, 14)  # 3s - 1s offset, 12s uzunluq


def test_cut_clip_handles_missing_video(data_dirs):
    assert media.cut_clip("/nonexistent/video.mp4", 5) is None
    assert media.cut_clip(None, 5) is None


def test_clear_dirs(data_dirs, sample_video):
    media.cut_clip(sample_video, 1)
    media.extract_wav_from_video(sample_video)
    media.clear_clips()
    media.clear_work_dir()
    assert not list(data_dirs.joinpath("clips").iterdir())
    assert not list(data_dirs.joinpath("work").iterdir())
