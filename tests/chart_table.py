"""Per-written-bar chart specs. Truth files expand these; they do not invent pitches."""

from __future__ import annotations

from dataclasses import dataclass

from sheet_score import Hit, bar8, expand_play_order, sustain


@dataclass(frozen=True)
class BarSpec:
    """One written 4/4 bar (1-based ``written``).

    ``lock=score``: printed TAB/chords; these hits are scored.
    ``lock=approx``: print not locked. Rhythm is ``skip`` — the bar keeps
    its place on the timeline but must not invent pitches to grade against.

    ``rhythm=hits``: irregular fill. ``events`` is
    ``(eighth, dur_eighths, pitch)`` in 0–8 eighths; ``pitches`` is that
    sequence (for snapshots).

    ``rhythm=split8``: four 8ths of pitch A, four 8ths of pitch B.
    ``rhythm=half_ee``: half note A, then two staccato 8ths of B (beat 4 rest).
    """

    written: int
    rhythm: str  # rest | eight | pair | whole | half | skip | hits | split8 | half_ee
    pitches: tuple[int, ...]
    lock: str
    comment: str = ""
    events: tuple[tuple[float, float, int], ...] = ()


def spec_hits(spec: BarSpec, play_bar: int) -> list[Hit]:
    if spec.rhythm in ("rest", "skip"):
        return []
    if spec.rhythm == "eight":
        assert len(spec.pitches) == 1, spec
        return bar8(spec.pitches[0], play_bar)
    if spec.rhythm == "pair":
        assert len(spec.pitches) == 2, spec
        a, b = spec.pitches
        return [
            sustain(a, play_bar, 0.0, 4.0),
            sustain(b, play_bar, 4.0, 4.0),
        ]
    if spec.rhythm == "split8":
        assert len(spec.pitches) == 2, spec
        a, b = spec.pitches
        return [Hit(play_bar, float(i), 1.0, a) for i in range(4)] + [
            Hit(play_bar, float(i), 1.0, b) for i in range(4, 8)
        ]
    if spec.rhythm == "half_ee":
        assert len(spec.pitches) == 2, spec
        a, b = spec.pitches
        return [
            sustain(a, play_bar, 0.0, 4.0),
            Hit(play_bar, 4.0, 1.0, b),
            Hit(play_bar, 5.0, 1.0, b),
        ]
    if spec.rhythm == "whole":
        assert len(spec.pitches) == 1, spec
        return [sustain(spec.pitches[0], play_bar, 0.0, 8.0)]
    if spec.rhythm == "half":
        assert len(spec.pitches) == 1, spec
        return [sustain(spec.pitches[0], play_bar, 0.0, 4.0)]
    if spec.rhythm == "hits":
        assert spec.events, spec
        return [
            Hit(play_bar, float(eighth), float(dur), int(pitch))
            for eighth, dur, pitch in spec.events
        ]
    raise ValueError(spec.rhythm)


def played_from_specs(specs: list[BarSpec], play_written_1based: list[int]) -> list[Hit]:
    lists = [spec_hits(spec, spec.written - 1) for spec in specs]
    order = [w - 1 for w in play_written_1based]
    return expand_play_order(lists, order)


def require_contiguous(specs: list[BarSpec]) -> None:
    assert [s.written for s in specs] == list(range(1, len(specs) + 1))
    for spec in specs:
        if spec.lock == "approx":
            assert spec.rhythm == "skip" and spec.pitches == (), spec
        if spec.lock == "score":
            assert spec.rhythm != "skip", spec
        if spec.rhythm in ("pair", "split8", "half_ee"):
            assert len(spec.pitches) == 2, spec
        if spec.rhythm == "hits":
            assert spec.events, spec
            assert spec.pitches == tuple(p for _, _, p in spec.events), spec
