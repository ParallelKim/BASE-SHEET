"""Published 자우림 「잊지」 bass tab (akbobada): q≈83, F# minor, 4/4.

Bars 1–12 tacet (not scored — the stem may still have tone). Verse is
sparse roots; chorus is driving 8ths. Fills at phrase ends use the bar
root. Do not commit the stem.
"""

from sheet_score import Hit, bar8, sustain

SCORE_BPM = 84.0
SCORE_KEY = "F# minor"
TACET_BARS = 12

FS, D, A, E = 30, 38, 33, 28  # F#1, D2, A1, E1
BM, GS = 35, 32  # B1 (A-string 2), G#1 (E/G#)

# Legacy aliases used by the old verse-only helper.
VERSE_BAR_ROOTS = [FS, D, A, E] * 3
CHORUS_BAR_ROOTS = [D, FS, E, BM]


def _half(p: int, bar: int) -> list[Hit]:
    return [sustain(p, bar, 0.0, 4.0)]


def played_hits() -> list[Hit]:
    hits: list[Hit] = []
    bar = 0

    def skip(n: int) -> None:
        nonlocal bar
        bar += n

    def halves(*pitches: int) -> None:
        nonlocal bar
        for p in pitches:
            hits.extend(_half(p, bar))
            bar += 1

    def eights(*pitches: int) -> None:
        nonlocal bar
        for p in pitches:
            hits.extend(bar8(p, bar))
            bar += 1

    def wholes(*pitches: int) -> None:
        nonlocal bar
        for p in pitches:
            hits.append(sustain(p, bar, 0.0, 8.0))
            bar += 1

    # p.1 mm.1–12 tacet
    skip(12)
    # mm.13–24 verse | F#m | D | A | E | ×3 (half-note roots)
    halves(*[FS, D, A, E] * 3)
    # p.2 mm.25–32 chorus 8ths | D | F#m | E | Bm | ×2
    eights(*[D, FS, E, BM] * 2)
    # mm.33–36 instrumental, verse rhythm
    halves(FS, D, A, E)
    # p.3 mm.37–44 inst / verse
    halves(*[FS, D, A, E] * 2)
    # mm.45–52 driving 8ths | F#m | E | A | D | F#m | E | Bm | (fill bar)
    eights(FS, E, A, D, FS, E, BM, BM)
    # mm.53–56 | F#m | E/G# | A | D | then F#m E Bm fill
    eights(FS, GS, A, D)
    # p.4 mm.57–60 8ths
    eights(FS, GS, A, D)
    # mm.61–72 long tones over F#m D A E
    wholes(*[FS, D, A, E] * 3)
    return hits


SECTIONS = {
    "verse": (12, 24),
    "chorus": (24, 32),
    "inst": (32, 44),
    "drive": (44, 60),
    "coda": (60, 72),
}
