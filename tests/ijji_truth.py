"""있지: expand ``ijji_chart`` (do not add pitches here)."""

from chart_table import played_from_specs, require_contiguous
from ijji_chart import BARS, PLAY, SECTIONS  # noqa: F401

SCORE_BPM = 84.0
SCORE_KEY = "F# minor"
TACET_BARS = 12
N_BARS = 72

FS, D, A, E = 30, 38, 33, 28
BM, GS = 35, 32
VERSE_BAR_ROOTS = [FS, D, A, E] * 3
CHORUS_BAR_ROOTS = [D, FS, E, BM]


def played_hits():
    require_contiguous(BARS)
    return played_from_specs(BARS, PLAY)
