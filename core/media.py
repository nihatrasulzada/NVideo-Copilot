"""Video/audio əməliyyatları: yükləmə, audio çıxarma, YouTube, klip kəsmə, təmizlik."""
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

import imageio_ffmpeg
import yt_dlp

import config
from core.models import Clip


class MediaError(RuntimeError):
    """Media əməliyyatı uğursuz oldu."""


def ensure_dirs() -> None:
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    config.CLIPS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_remove(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass  # Fayl istifadədədirsə (məs. Windows) xətanı gözardı et


def _clear_dir(directory: Path) -> None:
    if directory.exists():
        for item in directory.iterdir():
            if item.is_file():
                _safe_remove(item)
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)


def clear_work_dir() -> None:
    """Köhnə video və audio fayllarını silir."""
    _clear_dir(config.WORK_DIR)


def clear_clips() -> None:
    """Köhnə klipləri silir."""
    _clear_dir(config.CLIPS_DIR)


def _run_ffmpeg(args: list, timeout: int = 900) -> bool:
    """FFmpeg-i icra edir. Uğurlu olub-olmadığını qaytarır."""
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", *args]
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


def save_uploaded_file(uploaded_file) -> str:
    """Yüklənən faylı iş qovluğuna yazır və yolunu qaytarır."""
    ensure_dirs()
    suffix = Path(uploaded_file.name).suffix.lower() or ".mp4"
    path = config.WORK_DIR / f"{config.UPLOAD_VIDEO_STEM}{suffix}"
    path.write_bytes(uploaded_file.getbuffer())
    return str(path)


def extract_wav_from_video(video_path: str) -> Optional[str]:
    """Videodan 16kHz Mono WAV çıxarır. Audio yoxdursa None qaytarır."""
    ensure_dirs()
    out = config.WORK_DIR / config.EXTRACTED_AUDIO_NAME
    _safe_remove(out)
    ok = _run_ffmpeg([
        "-i", video_path,
        "-vn",                    # Görüntünü ləğv et
        "-acodec", "pcm_s16le",   # 16-bit WAV
        "-ar", "16000",           # 16 kHz (Whisper üçün)
        "-ac", "1",               # Mono
        str(out),
    ])
    if ok and out.exists() and out.stat().st_size > 44:  # 44 bayt = boş WAV başlığı
        return str(out)
    return None


def download_youtube(url: str) -> tuple[str, Optional[str]]:
    """YouTube videosunu yükləyir. (video_yolu, audio_yolu_və_ya_None) qaytarır."""
    ensure_dirs()
    template = config.WORK_DIR / f"{config.YT_VIDEO_STEM}.%(ext)s"
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
        "outtmpl": str(template),
        "noplaylist": True,  # Playlist linki verilsə yalnız bir video yüklə
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
        "nocheckcertificate": config.YT_NO_CHECK_CERTIFICATE,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    candidates = sorted(config.WORK_DIR.glob(f"{config.YT_VIDEO_STEM}.*"))
    if not candidates:
        raise MediaError("YouTube download finished but no video file was found.")
    video_path = str(candidates[0])
    return video_path, extract_wav_from_video(video_path)


def cut_clip(video_path: Optional[str], start_sec: int) -> Optional[Clip]:
    """Videodan `start_sec` anından klip kəsir. Alınmasa None qaytarır."""
    if not video_path or not Path(video_path).exists():
        return None

    ensure_dirs()
    start = max(0, int(start_sec) - config.CLIP_OFFSET_SEC)
    end = start + config.CLIP_DURATION_SEC
    out = config.CLIPS_DIR / f"clip_{start}_{uuid.uuid4().hex[:8]}.mp4"

    ok = _run_ffmpeg([
        "-ss", str(start), "-i", video_path, "-t", str(config.CLIP_DURATION_SEC),
        "-c:v", "libx264", "-c:a", "aac", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",  # Brauzerdə düzgün oynasın
        str(out),
    ])
    if ok and out.exists():
        return Clip(str(out), start, end)
    return None
