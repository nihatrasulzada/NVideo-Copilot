from core.formatting import (
    build_context,
    build_transcript,
    extract_citations,
    format_clock,
    pick_clip_starts,
    to_srt,
)
from core.models import Segment


def make_segments(n=5, text="hello world"):
    return [Segment(i, i * 10, i * 10 + 8, f"{text} {i}") for i in range(n)]


def test_format_clock():
    assert format_clock(0) == "0:00"
    assert format_clock(75) == "1:15"
    assert format_clock(3725) == "1:02:05"
    assert format_clock(-5) == "0:00"


def test_build_transcript_and_srt():
    segs = make_segments(2)
    assert build_transcript(segs) == "[0s]: hello world 0\n[10s]: hello world 1"
    srt = to_srt(segs)
    assert "1\n00:00:00,000 --> 00:00:08,000\nhello world 0" in srt
    assert "2\n00:00:10,000 --> 00:00:18,000\nhello world 1" in srt


def test_extract_citations_dedupes_and_filters():
    text = "Step one [12s]. Step two [30s-40s]. Again [12s]. Fake [9999s]."
    assert extract_citations(text) == [12, 30, 9999]
    assert extract_citations(text, max_ts=100) == [12, 30]
    assert extract_citations("no citations here") == []


def test_pick_clip_starts_respects_gap_and_limit():
    assert pick_clip_starts([10, 12, 30, 31, 60], limit=3, min_gap=6) == [10, 30, 60]
    assert pick_clip_starts([10, 30, 60], limit=2, min_gap=6) == [10, 30]
    assert pick_clip_starts([], limit=3, min_gap=6) == []


def test_build_context_short_transcript_is_full():
    segs = make_segments(3)
    assert build_context(segs, [1], char_limit=10_000) == build_transcript(segs)


def test_build_context_long_transcript_uses_hits_and_neighbors():
    segs = make_segments(100)
    ctx = build_context(segs, [50], char_limit=200, neighbors=1)
    lines = ctx.split("\n")
    assert [s.line for s in segs[49:52]] == lines
    assert len(ctx) <= 200


def test_build_context_marks_gaps_in_time_order():
    segs = make_segments(100)
    ctx = build_context(segs, [80, 10], char_limit=400, neighbors=0)
    assert ctx.split("\n") == [segs[10].line, "...", segs[80].line]


def test_build_context_without_hits_truncates():
    segs = make_segments(100)
    assert len(build_context(segs, [], char_limit=100)) <= 100
