"""Videonun indekslənməsi: Whisper ilə nitq və ya vision modeli ilə kadr təsvirləri."""
import math
import re
from functools import lru_cache
from typing import Callable, Iterator, Optional

import cv2

import config
from core import llm
from core.models import Segment

ProgressCb = Optional[Callable[[float], None]]

_NOISE_RE = re.compile(r"^[\d\s\.\-\*×x]+$")  # Yalnız rəqəm/simvoldan ibarət uydurma sətirlər


@lru_cache(maxsize=2)
def load_whisper(model_size: str):
    """Whisper modelini lazım olanda yükləyir və yadda saxlayır (başlanğıcı yavaşlatmır)."""
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe_audio(
    audio_path: str,
    model_size: str = config.DEFAULT_WHISPER_MODEL,
    language: Optional[str] = None,
    on_progress: ProgressCb = None,
) -> tuple[list[Segment], Optional[str]]:
    """Audionu mətnə çevirir. (seqmentlər, aşkarlanan dil) qaytarır."""
    model = load_whisper(model_size)
    raw_segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language=language,
        vad_filter=True,                                   # Yalnız nitq olan yerlər
        vad_parameters=dict(min_silence_duration_ms=500),
        no_speech_threshold=0.6,
        condition_on_previous_text=False,                  # Halüsinasiyaların qarşısını alır
    )

    segments: list[Segment] = []
    for raw in raw_segments:
        if on_progress and info.duration:
            on_progress(min(raw.end / info.duration, 1.0))
        text = raw.text.strip()
        if text and not _NOISE_RE.match(text):
            segments.append(Segment(len(segments), raw.start, raw.end, text))
    return segments, info.language


def get_duration(video_path: str) -> float:
    """Videonun müddətini saniyə ilə qaytarır (oxuna bilmirsə 0)."""
    cap = cv2.VideoCapture(video_path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        return frames / fps if fps > 0 else 0.0
    finally:
        cap.release()


def _encode_frame(frame) -> bytes:
    """Kadrı kiçildib JPEG baytlarına çevirir (API-yə göndərmək üçün)."""
    height, width = frame.shape[:2]
    if width > config.VISION_FRAME_MAX_WIDTH:
        scale = config.VISION_FRAME_MAX_WIDTH / width
        frame = cv2.resize(frame, (config.VISION_FRAME_MAX_WIDTH, int(height * scale)))
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not ok:
        raise RuntimeError("Could not encode video frame.")
    return buf.tobytes()


def sample_frames(video_path: str, interval: int) -> Iterator[tuple[int, bytes]]:
    """Hər `interval` saniyədən bir (saniyə, JPEG) cütü verir."""
    cap = cv2.VideoCapture(video_path)
    try:
        duration = get_duration(video_path)
        sec = 0
        while sec < duration:
            cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
            ret, frame = cap.read()
            if not ret:
                break
            yield sec, _encode_frame(frame)
            sec += interval
    finally:
        cap.release()


def describe_video(video_path: str, api_key: str, on_progress: ProgressCb = None) -> list[Segment]:
    """Səssiz rejim: kadrları vision modeli ilə təsvir edib seqmentlərə çevirir."""
    duration = get_duration(video_path)
    if duration <= 0:
        raise RuntimeError("Could not read the video file.")

    interval = max(config.FRAME_INTERVAL_SEC, math.ceil(duration / config.MAX_VISION_FRAMES))
    total = max(1, math.ceil(duration / interval))

    segments: list[Segment] = []
    failures = 0
    last_error: Optional[Exception] = None

    for n, (sec, jpeg) in enumerate(sample_frames(video_path, interval)):
        try:
            text = llm.describe_frame(api_key, jpeg)
            if text:
                segments.append(Segment(len(segments), sec, sec + interval, text))
        except llm.FATAL_ERRORS:
            raise
        except Exception as err:  # Bir kadr alınmasa digərlərinə davam et
            failures += 1
            last_error = err
            if not segments and failures >= 3:
                raise
        if on_progress:
            on_progress(min((n + 1) / total, 1.0))

    if not segments and last_error is not None:
        raise last_error
    return segments
