import subprocess

import imageio_ffmpeg
import pytest

import config


@pytest.fixture
def data_dirs(tmp_path, monkeypatch):
    """Testlər real data/ qovluğuna toxunmasın."""
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "WORK_DIR", tmp_path / "work")
    monkeypatch.setattr(config, "CLIPS_DIR", tmp_path / "clips")
    monkeypatch.setattr(config, "CHROMA_PATH", str(tmp_path / "chroma"))
    return tmp_path


@pytest.fixture
def sample_video(tmp_path):
    """ffmpeg ilə 6 saniyəlik rəngli video + sinus səsi yaradır."""
    path = tmp_path / "sample.mp4"
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "testsrc=duration=6:size=320x240:rate=10",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path),
    ]
    subprocess.run(cmd, check=True)
    return str(path)


@pytest.fixture
def silent_video(tmp_path):
    """Audio axını olmayan video."""
    path = tmp_path / "silent.mp4"
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "testsrc=duration=6:size=320x240:rate=10",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
    ]
    subprocess.run(cmd, check=True)
    return str(path)
