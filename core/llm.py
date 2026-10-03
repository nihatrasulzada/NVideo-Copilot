"""Groq LLM ilə əlaqə: mətn cavabı və kadr təsviri (vision)."""
import base64
import re
from functools import lru_cache

import groq
from groq import Groq

import config

# Bu xətalarda təkrar cəhd mənasızdır (açar səhvdir və ya icazə yoxdur)
FATAL_ERRORS = (groq.AuthenticationError, groq.PermissionDeniedError)


def clean_thinking_tags(text: str) -> str:
    """Cavabdan <think> və <thought> bloklarını silir."""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<thought>.*?</thought>", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()


def describe_error(err: Exception) -> str:
    """Texniki xətanı istifadəçi üçün anlaşılan mesaja çevirir."""
    if isinstance(err, groq.AuthenticationError):
        return "Groq API key is invalid. Please check the key in the sidebar."
    if isinstance(err, groq.RateLimitError):
        return "Groq rate limit reached. Wait a minute and try again."
    if isinstance(err, groq.APIConnectionError):
        return "Could not reach Groq. Check your internet connection."
    if isinstance(err, groq.NotFoundError):
        return f"Model not found on Groq ({err}). Set NVIDEO_VISION_MODEL in .env if the model was renamed."
    if isinstance(err, groq.APIStatusError):
        return f"Groq API error ({err.status_code}): {err}"
    return str(err)


@lru_cache(maxsize=4)
def _client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


@lru_cache(maxsize=4)
def select_model(api_key: str) -> str:
    """Mövcud modellərdən üstünlük sırasına görə mətn modelini seçir (nəticə keşlənir)."""
    available = [m.id for m in _client(api_key).models.list().data]
    usable = [
        m for m in available
        if not any(x in m.lower() for x in config.EXCLUDED_MODEL_KEYWORDS)
    ]
    return next(
        (pref for pref in config.PREFERRED_MODELS if pref in usable),
        usable[0] if usable else config.DEFAULT_MODEL,
    )


def ask(api_key: str, context: str, question: str) -> str:
    """Transkript konteksti əsasında suala cavab qaytarır."""
    prompt = f"Transcript:\n{context}\n\nUser Question: {question}"
    response = _client(api_key).chat.completions.create(
        messages=[
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        model=select_model(api_key),
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
    )
    return clean_thinking_tags((response.choices[0].message.content or "").strip())


def describe_frame(api_key: str, jpeg_bytes: bytes) -> str:
    """Bir video kadrını vision modeli ilə qısa təsvir edir."""
    b64 = base64.b64encode(jpeg_bytes).decode("ascii")
    response = _client(api_key).chat.completions.create(
        model=config.VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": config.VISION_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }],
        temperature=0.0,
        max_tokens=config.VISION_MAX_TOKENS,
    )
    return clean_thinking_tags((response.choices[0].message.content or "").strip())
