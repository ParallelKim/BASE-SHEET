"""Antifreeze: expand ``antifreeze_chart`` (do not add pitches here)."""

from chart_table import played_from_specs, require_contiguous
from antifreeze_chart import BARS, PLAY, SECTIONS  # noqa: F401
from sheet_score import Hit

SCORE_BPM = 128.0
SCORE_KEY = "F#"
B, CS, FS, EN = 35, 37, 30, 28
AS, GS, DS = 34, 32, 39
INTRO_BAR_ROOTS = [B, CS, FS, EN] * 4


def written_bars() -> list[list[Hit]]:
    from chart_table import spec_hits

    require_contiguous(BARS)
    return [spec_hits(spec, spec.written - 1) for spec in BARS]


def play_order(n_written: int) -> list[int]:
    order = [w - 1 for w in PLAY]
    if len(BARS) != n_written:
        raise ValueError(n_written)
    return order


def played_hits():
    require_contiguous(BARS)
    return played_from_specs(BARS, PLAY)


def n_played_bars() -> int:
    return len(PLAY)
