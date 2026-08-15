"""Per-written-bar chart specs. Truth files expand these; they do not invent pitches."""

from __future__ import annotations

from dataclasses import dataclass

from sheet_score import Hit, bar8, expand_play_order, sustain


@dataclass(frozen=True)
class BarSpec:
    """One written 4/4 bar (1-based ``written``).

    ``lock``:
      score  — read from the printed TAB/chords
      approx — simplified (fills, coda licks); not evidence against the pipeline
    """

    written: int
    rhythm: str  # rest | eight | pair | whole | downbeat
    pitches: tuple[int, ...]
    lock: str
    comment: str = ""


def spec_hits(spec: BarSpec, play_bar: int) -> list[Hit]:
    if spec.rhythm == "rest":
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
    if spec.rhythm in ("whole", "downbeat"):
        assert len(spec.pitches) == 1, spec
        return [sustain(spec.pitches[0], play_bar, 0.0, 8.0)]
    raise ValueError(spec.rhythm)


def played_from_specs(specs: list[BarSpec], play_written_1based: list[int]) -> list[Hit]:
    lists = [spec_hits(spec, spec.written - 1) for spec in specs]
    order = [w - 1 for w in play_written_1based]
    return expand_play_order(lists, order)


def require_contiguous(specs: list[BarSpec]) -> None:
    assert [s.written for s in specs] == list(range(1, len(specs) + 1))
