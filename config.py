"""Bütün sabit parametrlər bir yerdə."""
import os
from pathlib import Path

try:  # .env faylı varsa oxu (GROQ_API_KEY və s.). Paket yoxdursa sakitcə keç.
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

# --- Səhifə ---
PAGE_TITLE = "NVideo Copilot"
PAGE_ICON = "🎬"

# --- Fayl yolları (hamısı data/ qovluğunda, git-ə düşmür) ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
WORK_DIR = DATA_DIR / "work"      # Yüklənən video, çıxarılan audio
CLIPS_DIR = DATA_DIR / "clips"    # Kəsilmiş kliplər
CHROMA_PATH = str(DATA_DIR / "chroma_db")
COLLECTION_NAME = "nvideo_transcript"

UPLOAD_VIDEO_STEM = "uploaded_video"
EXTRACTED_AUDIO_NAME = "extracted_audio.wav"
YT_VIDEO_STEM = "yt_downloaded_video"

# --- Yükləmə ---
ALLOWED_VIDEO_TYPES = ["mp4", "mov", "mkv", "webm", "avi"]
# SSL yoxlamasını söndürmək təhlükəlidir. Yalnız korporativ şəbəkədə xəta alırsansa True et.
YT_NO_CHECK_CERTIFICATE = False

# --- Whisper ---
WHISPER_MODEL_SIZES = ["tiny", "base", "small", "medium"]
DEFAULT_WHISPER_MODEL = "base"  # Azərbaycan dili üçün "small" daha dəqiqdir
WHISPER_LANGUAGES = {
    "Auto-detect": None,
    "Azərbaycanca": "az",
    "English": "en",
    "Türkçe": "tr",
    "Русский": "ru",
}

# --- Emal parametrləri ---
FRAME_INTERVAL_SEC = 4      # Səssiz rejimdə minimum kadr aralığı (saniyə)
MAX_VISION_FRAMES = int(os.getenv("NVIDEO_MAX_VISION_FRAMES", "12"))  # Hər şəkil ~2048 token tutur
VISION_FRAME_MAX_WIDTH = 768
CLIP_DURATION_SEC = 12      # Kəsilən klipin uzunluğu
CLIP_OFFSET_SEC = 1         # Klip tapılan anın neçə saniyə əvvəlindən başlasın
MAX_CLIPS = 3               # Bir cavab üçün maksimum klip sayı
MIN_CLIP_GAP_SEC = 6        # Bir-birinə bundan yaxın klipləri birləşdirir
TOP_K_RESULTS = 8           # ChromaDB-dən neçə seqment gətirilsin
CONTEXT_NEIGHBORS = 2       # Tapılan seqmentin hər tərəfindən neçə qonşu seqment əlavə olunsun
CONTEXT_CHAR_LIMIT = 16000  # Bundan qısa transkript LLM-ə tam göndərilir, uzun olarsa yalnız uyğun hissələr

# --- Emal rejimləri ---
MODE_AUDIO = "🎙️ Audio & Speech Analysis (Whisper STT)"
MODE_SILENT = "🔕 Silent / Visual Frames (Frame Extraction)"
PROCESSING_MODES = [MODE_AUDIO, MODE_SILENT]

# --- Vektor axtarışı (istəyə bağlı) ---
# True etsən və `pip install sentence-transformers` qursan, Azərbaycan dilində axtarış daha yaxşı işləyər.
USE_MULTILINGUAL_EMBEDDINGS = os.getenv("NVIDEO_MULTILINGUAL", "0") == "1"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# --- LLM (mətn) ---
PREFERRED_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]
EXCLUDED_MODEL_KEYWORDS = [
    "whisper", "safetensors", "orpheus", "llama-4", "preview",
    "classify", "classifier", "guard", "deepseek-r1", "r1",
    "qwen", "vision",  # vision modelləri mətn cavabı üçün seçilməsin
]
DEFAULT_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.0
LLM_MAX_TOKENS = 1024

SYSTEM_PROMPT = (
    "You are NVideo Copilot. Answer based ONLY on the transcript. "
    "If the answer is not in the transcript, say so clearly instead of guessing. "
    "End every step or claim with the timestamp it comes from, written exactly like [12s]. "
    "Do not include <think> or <thought> tags. "
    "Format strictly as:\n"
    "🇦🇿 **Azərbaycan dilində izah:**\n[Steps]\n---\n🇬🇧 **English Translation:**\n[Steps]"
)

# --- LLM (vision, səssiz rejim üçün) ---
# Groq-da hazırda yeganə vision modeli. Dəyişsə, .env faylında NVIDEO_VISION_MODEL yaz.
VISION_MODEL = os.getenv("NVIDEO_VISION_MODEL", "qwen/qwen3.8-27b")
VISION_MAX_TOKENS = 600
VISION_PROMPT = (
    "Describe this video frame in 1-2 factual sentences: visible objects, people, actions, "
    "on-screen text and the setting. Do not speculate."
)
