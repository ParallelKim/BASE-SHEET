"""Score BASE-SHEET against the published 「잊지」 bass tab."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from base_sheet.models import NoteEvent
from ijji_truth import (
    CHORUS_BAR_ROOTS,
    SCORE_BPM,
    TACET_BARS,
    VERSE_BAR_ROOTS,
)

UPLOAD_STEM = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "______-________-bass-F__minor-84bpm-440hz_9aa2.m4a"
)
FIXTURE = Path(__file__).parent / "fixtures" / "ijji_bass.m4a"


def fixture_path() -> Path | None:
    if FIXTURE.is_file():
        return FIXTURE
    if UPLOAD_STEM.is_file():
        return UPLOAD_STEM
    return None


@dataclass
class IjjiScore:
    t0: float
    verse_acc: float
    chorus_acc: float
    verse_matched: int
    verse_n: int
    listen_within_semitone: float | None


def _pitch_at(notes: list[NoteEvent], t: float) -> int | None:
    hits = [n.pitch for n in notes if n.start - 1e-6 <= t < n.end]
    return hits[0] if hits else None


def _bar_s(bpm: float) -> float:
    return 4.0 * 60.0 / bpm


def score_bar_roots(
    notes: list[NoteEvent],
    roots: list[int],
    *,
    t0: float,
    first_bar: int,
    bpm: float = SCORE_BPM,
) -> tuple[float, int, int]:
    bar = _bar_s(bpm)
    matched = 0
    for i, root in enumerate(roots):
        t = t0 + (first_bar + i) * bar + 0.30 * bar
        pred = _pitch_at(notes, t)
        if pred == root:
            matched += 1
    n = len(roots)
    return (matched / n if n else 0.0), matched, n


def choose_t0(notes: list[NoteEvent], bpm: float = SCORE_BPM) -> float:
    bar = _bar_s(bpm)
    eighth = bar / 8.0
    first = notes[0].start if notes else 0.0
    candidates = [0.0, first] + [i * eighth for i in range(16)]
    best_t, best_acc = 0.0, -1.0
    for cand in candidates:
        acc, _, _ = score_bar_roots(
            notes, VERSE_BAR_ROOTS, t0=cand, first_bar=TACET_BARS, bpm=bpm
        )
        if acc > best_acc:
            best_acc = acc
            best_t = cand
    return best_t


def score_notes(
    notes: list[NoteEvent],
    *,
    bpm: float = SCORE_BPM,
    listen_within: float | None = None,
) -> IjjiScore:
    t0 = choose_t0(notes, bpm)
    verse_acc, verse_m, verse_n = score_bar_roots(
        notes, VERSE_BAR_ROOTS, t0=t0, first_bar=TACET_BARS, bpm=bpm
    )
    chorus_acc, _, _ = score_bar_roots(
        notes,
        CHORUS_BAR_ROOTS,
        t0=t0,
        first_bar=TACET_BARS + len(VERSE_BAR_ROOTS),
        bpm=bpm,
    )
    return IjjiScore(
        t0=t0,
        verse_acc=verse_acc,
        chorus_acc=chorus_acc,
        verse_matched=verse_m,
        verse_n=verse_n,
        listen_within_semitone=listen_within,
    )
