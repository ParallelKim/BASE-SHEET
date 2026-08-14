"""Eighth-grid comparison against the published Antifreeze bass tab."""

from __future__ import annotations

from dataclasses import dataclass

import pretty_midi

from antifreeze_truth import INTRO_BAR_ROOTS, SCORE_BPM


@dataclass
class IntroScore:
    t0: float
    pitch_acc: float
    matched: int
    missing: int
    mean_onsets_per_bar: float
    eighth_duration_frac: float


def _pitch_at(notes, t: float) -> int | None:
    hits = [n.pitch for n in notes if n.start - 1e-6 <= t < n.end]
    return hits[0] if hits else None


def score_intro_midi(midi_path, bpm: float = SCORE_BPM, n_bars: int = 16) -> IntroScore:
    pm = pretty_midi.PrettyMIDI(str(midi_path))
    notes = pm.instruments[0].notes
    eighth = 60.0 / bpm / 2.0
    bar = eighth * 8
    truth = []
    for root in INTRO_BAR_ROOTS[:n_bars]:
        truth.extend([root] * 8)

    first = notes[0].start if notes else 0.0
    candidates = [0.0, first] + [i * eighth for i in range(16)]

    def eval_t0(t0: float) -> tuple[float, int, int]:
        pred = [_pitch_at(notes, t0 + (i + 0.5) * eighth) for i in range(len(truth))]
        known = [p is not None for p in pred]
        match = [p == t for p, t in zip(pred, truth)]
        n_known = sum(known)
        acc = (sum(m for m, k in zip(match, known) if k) / n_known) if n_known else 0.0
        return acc, sum(match), sum(not k for k in known)

    t0, best = first, (-1.0, 0, 99)
    for cand in candidates:
        acc, matched, missing = eval_t0(cand)
        if (acc, matched, -missing) > (best[0], best[1], -best[2]):
            best = (acc, matched, missing)
            t0 = cand

    onsets = []
    for b in range(n_bars):
        a, z = t0 + b * bar, t0 + (b + 1) * bar
        onsets.append(sum(1 for n in notes if a - 1e-3 <= n.start < z))
    durs = [n.end - n.start for n in notes]
    eighth_frac = (
        sum(1 for d in durs if abs(d - eighth) < 0.05) / len(durs) if durs else 0.0
    )
    return IntroScore(
        t0=t0,
        pitch_acc=best[0],
        matched=best[1],
        missing=best[2],
        mean_onsets_per_bar=sum(onsets) / n_bars,
        eighth_duration_frac=eighth_frac,
    )
