"""자우림 「있지」 bass chart (akbobada, 4 pages, 72 bars, no repeats).

The identifier ``ijji`` is the romanization of 있지 — not 잊지.

MIDI: F#1=30 D2=38 A1=33 E1=28 B1=35 G#1=32 E2=40 A2=45 G#2=44 C#2=37 F#2=42.
lock=score was read from TAB + chord symbols.
"""

from chart_table import BarSpec

FS, D, A, E, BM, GS = 30, 38, 33, 28, 35, 32
E2, A2, GS2, CS, FS2 = 40, 45, 44, 37, 42


def _rest(w: int) -> BarSpec:
    return BarSpec(w, "rest", (), "score", "p.1 bass tacet")


def _pair(w: int, a: int, b: int, comment: str, lock: str = "score") -> BarSpec:
    return BarSpec(w, "pair", (a, b), lock, comment)


def _eight(w: int, p: int, comment: str, lock: str = "score") -> BarSpec:
    return BarSpec(w, "eight", (p,), lock, comment)


def _whole(w: int, p: int, comment: str, lock: str = "score") -> BarSpec:
    return BarSpec(w, "whole", (p,), lock, comment)


def _hits(w: int, events: list[tuple[float, float, int]], comment: str) -> BarSpec:
    ev = tuple((float(e), float(d), int(p)) for e, d, p in events)
    return BarSpec(w, "hits", tuple(p for _, _, p in ev), "score", comment, events=ev)


def _a_lick(w: int, comment: str) -> BarSpec:
    """A (E5) then TAB 7-6-7-0 = A2 G#2 E2 E1."""
    return _hits(
        w,
        [
            (0.0, 3.0, A),
            (3.0, 1.0, A2),
            (4.0, 1.0, GS2),
            (5.0, 1.0, E2),
            (6.0, 2.0, E),
        ],
        comment,
    )


def _bm_fill(w: int, comment: str) -> BarSpec:
    """Bm: A-string 2s then 5-4-0 (D C# E)."""
    return _hits(
        w,
        [
            (0.0, 1.0, BM),
            (1.0, 2.0, BM),
            (3.0, 1.0, BM),
            (4.0, 1.0, BM),
            (5.0, 1.0, BM),
            (6.0, 0.5, D),
            (6.5, 0.5, CS),
            (7.0, 1.0, E),
        ],
        comment,
    )


def _bars() -> list[BarSpec]:
    rows: list[BarSpec] = []

    rows.extend(_rest(w) for w in range(1, 13))

    w = 13
    for _ in range(6):
        rows.append(_pair(w, FS, D, "verse | F# D |"))
        w += 1
        if w == 16:
            rows.append(_a_lick(w, "verse | A + 7-6-7-0 fill |"))
        elif w == 24:
            rows.append(
                _hits(
                    w,
                    [
                        (0.0, 3.0, A),
                        (3.0, 1.0, E),
                        (4.0, 1.0, A2),
                        (5.0, 1.0, GS2),
                        (6.0, 1.0, E2),
                        (7.0, 1.0, E),
                    ],
                    "verse | A E + 7-6-7-0 fill |",
                )
            )
        else:
            rows.append(_pair(w, A, E, "verse | A E |"))
        w += 1

    for i, p in enumerate([D, FS, E, BM] * 2):
        wb = 25 + i
        if wb == 28:
            rows.append(_bm_fill(wb, "chorus Bm fill 2s + 5-4-0"))
        elif wb == 32:
            rows.append(
                _hits(
                    wb,
                    [
                        (0.0, 1.0, BM),
                        (1.0, 1.0, BM),
                        (2.0, 1.0, BM),
                        (3.0, 1.0, CS),
                        (4.0, 1.0, D),
                        (5.0, 1.0, D),
                        (6.0, 1.0, CS),
                        (7.0, 1.0, A),
                    ],
                    "chorus Bm fill 2s + 4-5-5-4",
                )
            )
        else:
            rows.append(_eight(wb, p, "chorus 8ths D|F#m|E|Bm"))

    w = 33
    for _ in range(6):
        rows.append(_pair(w, FS, D, "inst | F# D |"))
        w += 1
        if w == 36:
            rows.append(
                _hits(
                    w,
                    [
                        (0.0, 1.0, A),
                        (1.0, 1.0, A),
                        (3.0, 1.0, A2),
                        (4.0, 1.0, GS2),
                        (5.0, 1.0, E2),
                        (6.0, 1.0, E),
                        (7.0, 1.0, E),
                    ],
                    "inst | A A + 7-6-7-0 |",
                )
            )
        elif w == 40:
            rows.append(
                _hits(
                    w,
                    [
                        (0.0, 1.0, A),
                        (1.0, 1.0, A),
                        (2.0, 1.0, E2),
                        (3.0, 1.0, 47),  # D-string 9 = B2
                        (4.0, 1.0, 47),
                        (5.0, 1.0, A2),
                        (6.0, 1.0, GS2),
                    ],
                    "inst | A + 9-9-7-6 fill |",
                )
            )
        elif w == 44:
            rows.append(
                _hits(
                    w,
                    [
                        (0.0, 1.0, A),
                        (1.0, 1.0, A),
                        (4.0, 1.0, E),
                        (5.0, 1.0, A2),
                        (6.0, 1.0, E2),
                        (7.0, 1.0, E),
                    ],
                    "inst | A A + 0-7-7-0 fill |",
                )
            )
        else:
            rows.append(_pair(w, A, E, "inst | A E |"))
        w += 1

    for i, p in enumerate([FS, E, A, D, FS, E, BM, BM]):
        wb = 45 + i
        if wb == 48:
            rows.append(_bm_fill(wb, "drive fill: 2s + 5-4-0 (print TAB)"))
        elif wb == 52:
            rows.append(
                _hits(
                    wb,
                    [
                        (0.0, 1.0, BM),
                        (1.0, 1.0, BM),
                        (2.0, 1.0, BM),
                        (3.0, 1.0, BM),
                        (4.0, 1.0, BM),
                        (5.0, 1.0, BM),
                        (6.0, 0.5, A2),
                        (6.5, 0.5, GS2),
                        (7.0, 1.0, E),
                    ],
                    "drive Bm fill + 12-11-0",
                )
            )
        else:
            rows.append(_eight(wb, p, "drive 8ths"))

    for i, p in enumerate([FS, GS, A, D] * 2):
        rows.append(_eight(53 + i, p, "drive E/G# 8ths"))

    rows.append(_whole(61, FS, "coda F# pedal, tied"))
    rows.append(_whole(62, FS, "coda F# tied"))
    rows.append(_whole(63, FS, "coda F# tied"))
    rows.append(_pair(64, FS, A, "coda F# then A"))

    rows.append(_whole(65, FS2, "coda_b A-string 9 = F#2"))
    rows.append(_pair(66, E2, E, "coda_b A7 then E0"))
    rows.append(_whole(67, FS2, "coda_b A-string 9 = F#2"))
    rows.append(_pair(68, A, E2, "coda_b E5 then A7"))
    rows.append(_whole(69, FS2, "coda_b A-string 9 = F#2"))
    rows.append(_pair(70, A, E2, "coda_b E5 then A7"))
    rows.append(_whole(71, FS, "coda_b E-string 2 = F#1"))
    rows.append(_pair(72, A, E, "coda_b E5 then E0, final bar"))

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
    16: ("hits", (A, A2, GS2, E2, E)),
    17: ("pair", (FS, D)),
    18: ("pair", (A, E)),
    24: ("hits", (A, E, A2, GS2, E2, E)),
    25: ("eight", (D,)),
    26: ("eight", (FS,)),
    27: ("eight", (E,)),
    28: ("hits", (BM, BM, BM, BM, BM, D, CS, E)),
    29: ("eight", (D,)),
    32: ("hits", (BM, BM, BM, CS, D, D, CS, A)),
    33: ("pair", (FS, D)),
    34: ("pair", (A, E)),
    36: ("hits", (A, A, A2, GS2, E2, E, E)),
    40: ("hits", (A, A, E2, 47, 47, A2, GS2)),
    44: ("hits", (A, A, E, A2, E2, E)),
    45: ("eight", (FS,)),
    46: ("eight", (E,)),
    47: ("eight", (A,)),
    48: ("hits", (BM, BM, BM, BM, BM, D, CS, E)),
    52: ("hits", (BM, BM, BM, BM, BM, BM, A2, GS2, E)),
    53: ("eight", (FS,)),
    54: ("eight", (GS,)),
    55: ("eight", (A,)),
    56: ("eight", (D,)),
    61: ("whole", (FS,)),
    62: ("whole", (FS,)),
    63: ("whole", (FS,)),
    64: ("pair", (FS, A)),
    65: ("whole", (FS2,)),
    66: ("pair", (E2, E)),
    67: ("whole", (FS2,)),
    68: ("pair", (A, E2)),
    69: ("whole", (FS2,)),
    70: ("pair", (A, E2)),
    71: ("whole", (FS,)),
    72: ("pair", (A, E)),
}
