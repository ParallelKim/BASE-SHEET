"""Sectioned full-song scoring against published bass tabs."""

from __future__ import annotations

from dataclasses import dataclass

from base_sheet.models import NoteEvent
from sheet_score import Hit, SheetScore, choose_t0, score_hits


@dataclass
class SongScore:
    t0: float
    overall: SheetScore
    sections: dict[str, SheetScore]


def hits_in_bars(hits: list[Hit], start: int, end: int) -> list[Hit]:
    return [h for h in hits if start <= h.bar < end]


def score_song(
    notes: list[NoteEvent],
    hits: list[Hit],
    bpm: float,
    sections: dict[str, tuple[int, int]],
    *,
    t0: float | None = None,
) -> SongScore:
    if t0 is None:
        t0 = choose_t0(notes, hits, bpm)
    overall = score_hits(notes, hits, bpm, t0)
    part: dict[str, SheetScore] = {}
    for name, (a, b) in sections.items():
        part[name] = score_hits(notes, hits_in_bars(hits, a, b), bpm, t0)
    return SongScore(t0=t0, overall=overall, sections=part)
