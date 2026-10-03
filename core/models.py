"""Layihədə istifadə olunan məlumat strukturları."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    """Videonun bir hissəsi: nitq seqmenti və ya kadr təsviri."""

    index: int
    start: float
    end: float
    text: str

    @property
    def timestamp(self) -> int:
        return int(self.start)

    @property
    def line(self) -> str:
        return f"[{self.timestamp}s]: {self.text}"


@dataclass(frozen=True)
class Clip:
    """Videodan kəsilmiş klip."""

    path: str
    start: int
    end: int
