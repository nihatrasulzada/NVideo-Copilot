"""Təmiz (kənar asılılığı olmayan) köməkçi funksiyalar: format, sitat, kontekst."""
import re
from typing import Optional, Sequence

from core.models import Segment

_CITATION_RE = re.compile(r"\[(\d+)\s*s")  # [12s], [12 s], [12s-20s] -> 12


def format_clock(seconds: float) -> str:
    """75 -> '1:15', 3725 -> '1:02:05'."""
    total = int(max(0, seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _srt_time(seconds: float) -> str:
    total_ms = int(round(max(0.0, seconds) * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def build_transcript(segments: Sequence[Segment]) -> str:
    """Seqmentləri `[12s]: mətn` formatında birləşdirir."""
    return "\n".join(s.line for s in segments)


def to_srt(segments: Sequence[Segment]) -> str:
    """Seqmentləri SRT subtitr formatına çevirir."""
    blocks = []
    for n, seg in enumerate(segments, start=1):
        end = max(seg.end, seg.start + 0.5)
        blocks.append(f"{n}\n{_srt_time(seg.start)} --> {_srt_time(end)}\n{seg.text}\n")
    return "\n".join(blocks)


def extract_citations(text: str, max_ts: Optional[int] = None) -> list[int]:
    """LLM cavabındakı [12s] istinadlarını ardıcıllığı pozmadan, təkrarsız qaytarır."""
    seen: list[int] = []
    for match in _CITATION_RE.finditer(text):
        ts = int(match.group(1))
        if max_ts is not None and ts > max_ts:
            continue  # Videodan kənar (uydurma) vaxtı at
        if ts not in seen:
            seen.append(ts)
    return seen


def pick_clip_starts(candidates: Sequence[int], limit: int, min_gap: int) -> list[int]:
    """Bir-birinə çox yaxın olmayan ilk `limit` vaxtı seçir."""
    chosen: list[int] = []
    for ts in candidates:
        if all(abs(ts - kept) >= min_gap for kept in chosen):
            chosen.append(ts)
        if len(chosen) >= limit:
            break
    return chosen


def build_context(
    segments: Sequence[Segment],
    hit_indexes: Sequence[int],
    char_limit: int,
    neighbors: int = 2,
) -> str:
    """LLM üçün kontekst qurur.

    Transkript limitə sığırsa tam göndərilir. Sığmırsa axtarışda tapılan seqmentlər
    və onların qonşuları (uyğunluq sırası ilə, limitə çatana qədər) vaxt sırası ilə düzülür.
    """
    full = build_transcript(segments)
    if len(full) <= char_limit:
        return full

    chosen: set[int] = set()
    used = 0
    for hit in hit_indexes:
        for j in range(max(0, hit - neighbors), min(len(segments), hit + neighbors + 1)):
            if j in chosen:
                continue
            cost = len(segments[j].line) + 1
            if used + cost > char_limit:
                continue
            chosen.add(j)
            used += cost

    if not chosen:  # Axtarış nəticəsi yoxdur: transkriptin əvvəlini göndər
        return full[:char_limit]

    lines: list[str] = []
    prev: Optional[int] = None
    for j in sorted(chosen):
        if prev is not None and j != prev + 1:
            lines.append("...")
        lines.append(segments[j].line)
        prev = j
    return "\n".join(lines)
