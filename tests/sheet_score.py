"""Score transcribed notes against a published bass tab on an eighth grid."""

from __future__ import annotations

from dataclasses import dataclass

from base_sheet.models import NoteEvent

IGNORE = None  # unused; rests are simply omitted from Hit lists


@dataclass(frozen=True)
class Hit:
    """One sounding event. ``bar`` is 0-based; ``eighth`` is 0–7 in the bar."""

    bar: int
    eighth: float
    dur_eighths: float
    pitch: int


@dataclass
class SheetScore:
    t0: float
    n_hits: int
    sounding: int
    pitch_exact: float
    pitch_chroma: float
    pitch_within_semitone: float
    onset_f: float
    missing: int


def eighth_s(bpm: float) -> float:
    return 60.0 / float(bpm) / 2.0


def hit_time(hit: Hit, t0: float, bpm: float) -> float:
    return t0 + (hit.bar * 8.0 + hit.eighth) * eighth_s(bpm)


def pitch_at(notes: list[NoteEvent], t: float) -> int | None:
    hits = [n.pitch for n in notes if n.start - 1e-6 <= t < n.end]
    return hits[0] if hits else None


def bar8(pitch: int, bar: int) -> list[Hit]:
    return [Hit(bar, float(i), 1.0, pitch) for i in range(8)]


def sustain(pitch: int, bar: int, eighth: float, dur_eighths: float) -> Hit:
    return Hit(bar, eighth, dur_eighths, pitch)


def expand_play_order(written: list[list[Hit]], play_order: list[int]) -> list[Hit]:
    """Replay written bars in performance order, re-indexing bar numbers."""
    out: list[Hit] = []
    for new_bar, src in enumerate(play_order):
        for hit in written[src]:
            out.append(Hit(new_bar, hit.eighth, hit.dur_eighths, hit.pitch))
    return out


def _match_onsets(
    truth: list[Hit],
    pred: list[NoteEvent],
    t0: float,
    bpm: float,
    tol: float = 0.05,
) -> tuple[int, int, int]:
    starts = sorted(n.start for n in pred)
    used: set[int] = set()
    tp = 0
    for hit in truth:
        t = hit_time(hit, t0, bpm)
        best_i, best_d = None, tol + 1.0
        for i, s in enumerate(starts):
            if i in used:
                continue
            d = abs(s - t)
            if d <= tol and d < best_d:
                best_d, best_i = d, i
        if best_i is None:
            continue
        used.add(best_i)
        tp += 1
    return tp, len(pred), len(truth)


def _f(tp: int, n_pred: int, n_truth: int) -> float:
    if tp == 0 or n_pred == 0 or n_truth == 0:
        return 0.0
    p, r = tp / n_pred, tp / n_truth
    return 2.0 * p * r / (p + r)


def score_hits(
    notes: list[NoteEvent],
    hits: list[Hit],
    bpm: float,
    t0: float,
    *,
    onset_tol: float = 0.05,
) -> SheetScore:
    exact = chroma = near = sounding = 0
    missing = 0
    for hit in hits:
        t = hit_time(hit, t0, bpm) + 0.35 * hit.dur_eighths * eighth_s(bpm)
        pred = pitch_at(notes, t)
        if pred is None:
            missing += 1
            continue
        sounding += 1
        if pred == hit.pitch:
            exact += 1
        if pred % 12 == hit.pitch % 12:
            chroma += 1
        if abs(pred - hit.pitch) <= 1:
            near += 1
    n = len(hits)
    tp, n_pred, n_truth = _match_onsets(hits, notes, t0, bpm, onset_tol)
    return SheetScore(
        t0=t0,
        n_hits=n,
        sounding=sounding,
        pitch_exact=(exact / sounding) if sounding else 0.0,
        pitch_chroma=(chroma / sounding) if sounding else 0.0,
        pitch_within_semitone=(near / sounding) if sounding else 0.0,
        onset_f=_f(tp, n_pred, n_truth),
        missing=missing,
    )


def choose_t0(
    notes: list[NoteEvent],
    hits: list[Hit],
    bpm: float,
    *,
    window_eighths: int = 16,
) -> float:
    eighth = eighth_s(bpm)
    first = notes[0].start if notes else 0.0
    cands = [0.0, first] + [i * eighth for i in range(window_eighths)]
    best_t, best = 0.0, -1.0
    # Align on the first 8 sounding bars (not a fixed hit count: 8ths vs halves).
    if hits:
        min_bar = min(h.bar for h in hits)
        probe = [h for h in hits if h.bar < min_bar + 8]
        if not probe:
            probe = hits[:32]
    else:
        probe = hits
    for cand in cands:
        sc = score_hits(notes, probe, bpm, cand)
        key = sc.pitch_exact * 2.0 + sc.pitch_chroma
        if key > best:
            best, best_t = key, cand
    return best_t
