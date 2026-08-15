"""자우림 「있지」 bass chart (akbobada, 4 pages, 72 bars, no repeats).

The identifier ``ijji`` is the romanization of 있지 — not 잊지.

MIDI: F#1=30 D2=38 A1=33 E1=28 B1=35 G#1=32.
lock=score was read from TAB + chord symbols. lock=approx is not print-complete.
"""

from chart_table import BarSpec

FS, D, A, E, BM, GS = 30, 38, 33, 28, 35, 32


def _rest(w: int) -> BarSpec:
    return BarSpec(w, "rest", (), "score", "p.1 bass tacet")


def _pair(w: int, a: int, b: int, comment: str, lock: str = "score") -> BarSpec:
    return BarSpec(w, "pair", (a, b), lock, comment)


def _eight(w: int, p: int, comment: str, lock: str = "score") -> BarSpec:
    return BarSpec(w, "eight", (p,), lock, comment)


def _whole(w: int, p: int, comment: str, lock: str = "score") -> BarSpec:
    return BarSpec(w, "whole", (p,), lock, comment)


def _bars() -> list[BarSpec]:
    rows: list[BarSpec] = []

    rows.extend(_rest(w) for w in range(1, 13))

    w = 13
    for _ in range(6):
        rows.append(_pair(w, FS, D, "verse | F# D |"))
        w += 1
        fill = w in (16, 24)
        rows.append(
            _pair(
                w,
                A,
                E,
                "verse | A E | last-beat fill on print" if fill else "verse | A E |",
                lock="approx" if fill else "score",
            )
        )
        w += 1

    for i, p in enumerate([D, FS, E, BM] * 2):
        wb = 25 + i
        rows.append(
            _eight(
                wb,
                p,
                "chorus 8ths D|F#m|E|Bm",
                lock="approx" if wb in (28, 32) else "score",
            )
        )

    w = 33
    for _ in range(6):
        rows.append(_pair(w, FS, D, "inst | F# D |"))
        w += 1
        fill = w in (36, 40, 44)
        rows.append(
            _pair(
                w,
                A,
                E,
                "inst | A E |",
                lock="approx" if fill else "score",
            )
        )
        w += 1

    for i, p in enumerate([FS, E, A, D, FS, E, BM, BM]):
        wb = 45 + i
        rows.append(
            _eight(
                wb,
                p,
                "drive 8ths",
                lock="approx" if wb in (48, 52) else "score",
            )
        )

    for i, p in enumerate([FS, GS, A, D] * 2):
        rows.append(_eight(53 + i, p, "drive E/G# 8ths"))

    rows.append(_whole(61, FS, "coda F# pedal, tied"))
    rows.append(_whole(62, FS, "coda F# tied"))
    rows.append(_whole(63, FS, "coda F# tied"))
    rows.append(_pair(64, FS, A, "coda F# then A"))

    for wb, a, b in (
        (65, FS, None),
        (66, E, E),
        (67, FS, None),
        (68, A, E),
        (69, FS, None),
        (70, A, A),
        (71, FS, None),
        (72, A, E),
    ):
        if b is None:
            rows.append(_whole(wb, a, "coda sparse, unverified fret", lock="approx"))
        else:
            rows.append(_pair(wb, a, b, "coda sparse, unverified fret", lock="approx"))

    return rows


BARS = _bars()
PLAY = list(range(1, 73))

SECTIONS = {
    "tacet": (0, 12),
    "verse": (12, 24),
    "chorus": (24, 32),
    "inst": (32, 44),
    "drive": (44, 60),
    "coda_a": (60, 64),
    "coda_b": (64, 72),
}

# Independent freeze of score-locked bars. Re-read the print before changing these.
LOCK_SNAPSHOT: dict[int, tuple[str, tuple[int, ...]]] = {
    1: ("rest", ()),
    12: ("rest", ()),
    13: ("pair", (FS, D)),
    14: ("pair", (A, E)),
    15: ("pair", (FS, D)),
    17: ("pair", (FS, D)),
    18: ("pair", (A, E)),
    25: ("eight", (D,)),
    26: ("eight", (FS,)),
    27: ("eight", (E,)),
    29: ("eight", (D,)),
    33: ("pair", (FS, D)),
    34: ("pair", (A, E)),
    45: ("eight", (FS,)),
    46: ("eight", (E,)),
    47: ("eight", (A,)),
    53: ("eight", (FS,)),
    54: ("eight", (GS,)),
    55: ("eight", (A,)),
    56: ("eight", (D,)),
    61: ("whole", (FS,)),
    62: ("whole", (FS,)),
    63: ("whole", (FS,)),
    64: ("pair", (FS, A)),
}
