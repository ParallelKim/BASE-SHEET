"""Published 자우림 「잊지」 bass tab (akbobada): q=83, F# minor, 4/4.

Bars 1–12 tacet. Verse/inst harmonic rhythm on the TAB is two roots per
bar (| F# D | A E |), not one chord per bar. Chorus/drive are one chord
per bar of driving 8ths. Coda is sparse long tones (not 12 whole-note
F# D A E cycles). Do not commit the stem.
"""

from sheet_score import Hit, bar8, sustain

SCORE_BPM = 84.0  # stem is labeled 84; print metronome is 83
SCORE_KEY = "F# minor"
TACET_BARS = 12
N_BARS = 72

FS, D, A, E = 30, 38, 33, 28  # F#1, D2, A1, E1
BM, GS = 35, 32  # B1, G#1

# Legacy aliases: verse is two chords per written bar.
VERSE_BAR_ROOTS = [FS, D, A, E] * 3
CHORUS_BAR_ROOTS = [D, FS, E, BM]


def _half(p: int, bar: int, eighth: float = 0.0) -> Hit:
    return sustain(p, bar, eighth, 4.0)


def played_hits() -> list[Hit]:
    hits: list[Hit] = []
    bar = 0

    def skip(n: int) -> None:
        nonlocal bar
        bar += n

    def pair(a: int, b: int) -> None:
        """One bar: half-note a, half-note b (| F# D | or | A E |)."""
        nonlocal bar
        hits.append(_half(a, bar, 0.0))
        hits.append(_half(b, bar, 4.0))
        bar += 1

    def cycle_fs_d_a_e(n_cycles: int) -> None:
        for _ in range(n_cycles):
            pair(FS, D)
            pair(A, E)

    def eights(*pitches: int) -> None:
        nonlocal bar
        for p in pitches:
            hits.extend(bar8(p, bar))
            bar += 1

    def whole(p: int) -> None:
        nonlocal bar
        hits.append(sustain(p, bar, 0.0, 8.0))
        bar += 1

    # p.1 mm.1–12 tacet
    skip(12)
    # mm.13–24 verse: TAB | F# D | A E | ×6 (not | F# | D | A | E |)
    cycle_fs_d_a_e(6)
    # p.2 mm.25–32 chorus 8ths | D | F#m | E | Bm | ×2
    eights(*[D, FS, E, BM] * 2)
    # mm.33–44 inst / second verse: same two-in-a-bar rhythm
    cycle_fs_d_a_e(6)
    # p.3 mm.45–52 driving 8ths | F#m | E | A | D | F#m | E | Bm | Bm
    eights(FS, E, A, D, FS, E, BM, BM)
    # mm.53–60 | F#m | E/G# | A | D | ×2
    eights(FS, GS, A, D, FS, GS, A, D)
    # p.4 mm.61–64 tied F# pedal, last bar adds A
    whole(FS)
    whole(FS)
    whole(FS)
    hits.append(sustain(FS, bar, 0.0, 4.0))
    hits.append(sustain(A, bar, 4.0, 4.0))
    bar += 1
    # mm.65–68 sparse: F# | E E | F# | A E |
    whole(FS)
    pair(E, E)
    whole(FS)
    pair(A, E)
    # mm.69–72 sparse: F# | A A | F# | A E |
    whole(FS)
    pair(A, A)
    whole(FS)
    pair(A, E)
    if bar != N_BARS:
        raise RuntimeError(f"잊지 truth ended at bar {bar}, expected {N_BARS}")
    return hits


SECTIONS = {
    "tacet": (0, 12),
    "verse": (12, 24),
    "chorus": (24, 32),
    "inst": (32, 44),
    "drive": (44, 60),
    "coda_a": (60, 64),
    "coda_b": (64, 72),
}
