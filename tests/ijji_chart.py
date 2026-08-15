"""자우림 「있지」 bass chart (akbobada, 4 pages, 72 bars, no repeats).

The identifier ``ijji`` is the romanization of 있지 — not 잊지.

MIDI: F#1=30 D2=38 A1=33 E1=28 B1=35 G#1=32 E2=40 A2=45 G#2=44 C#2=37
F#2=42 G2=43 B2=47 C#3=49 D3=50.
lock=score was read from printed measure crops + page images.
"""

from chart_table import BarSpec

FS, D, A, E, BM, GS = 30, 38, 33, 28, 35, 32
E2, A2, GS2, CS, FS2 = 40, 45, 44, 37, 42
G2, B2, CS3, D3 = 43, 47, 49, 50


def _rest(w: int) -> BarSpec:
    return BarSpec(w, "rest", (), "score", "p.1 bass tacet")


def _pair(w: int, a: int, b: int, comment: str) -> BarSpec:
    return BarSpec(w, "pair", (a, b), "score", comment)


def _split8(w: int, a: int, b: int, comment: str) -> BarSpec:
    return BarSpec(w, "split8", (a, b), "score", comment)


def _half_ee(w: int, a: int, b: int, comment: str) -> BarSpec:
    return BarSpec(w, "half_ee", (a, b), "score", comment)


def _eight(w: int, p: int, comment: str) -> BarSpec:
    return BarSpec(w, "eight", (p,), "score", comment)


def _whole(w: int, p: int, comment: str) -> BarSpec:
    return BarSpec(w, "whole", (p,), "score", comment)


def _hits(w: int, events: list[tuple[float, float, int]], comment: str) -> BarSpec:
    ev = tuple((float(e), float(d), int(p)) for e, d, p in events)
    return BarSpec(w, "hits", tuple(p for _, _, p in ev), "score", comment, events=ev)


def _a_lick(w: int, comment: str) -> BarSpec:
    """A (E5 dotted quarter) then TAB D7-D6-A7-E0."""
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


def _bm_fill_28(w: int) -> BarSpec:
    """m028: quarter B, 8ths B, then 16ths D-C# (A5-A4). No final E."""
    return _hits(
        w,
        [
            (0.0, 2.0, BM),
            (2.0, 1.0, BM),
            (3.0, 1.0, BM),
            (4.0, 1.0, BM),
            (5.0, 1.0, BM),
            (6.0, 1.0, BM),
            (7.0, 0.5, D),
            (7.5, 0.5, CS),
        ],
        "chorus Bm fill: quarter + 8ths + 16ths 5-4",
    )


def _bars() -> list[BarSpec]:
    rows: list[BarSpec] = []

    rows.extend(_rest(w) for w in range(1, 13))

    # Verse 13–24. m013 crop: half F# then two staccato D 8ths (beat 4 rest).
    rows.append(_half_ee(13, FS, D, "verse | F# D | half + two 8ths"))
    rows.append(_half_ee(14, A, E, "verse | A E | half + two 8ths"))
    rows.append(_half_ee(15, FS, D, "verse | F# D | half + two 8ths"))
    rows.append(_a_lick(16, "verse | A + D7-D6-A7-E0 fill |"))
    rows.append(_half_ee(17, FS, D, "verse | F# D | half + two 8ths"))
    rows.append(_half_ee(18, A, E, "verse | A E | half + two 8ths"))
    rows.append(_half_ee(19, FS, D, "verse | F# D | half + two 8ths"))
    rows.append(_half_ee(20, A, E, "verse | A E | half + two 8ths"))
    rows.append(_half_ee(21, FS, D, "verse | F# D | half + two 8ths"))
    rows.append(_half_ee(22, A, E, "verse | A E | half + two 8ths"))
    rows.append(_half_ee(23, FS, D, "verse | F# D | half + two 8ths"))
    rows.append(
        _hits(
            24,
            [
                (0.0, 3.0, A),
                (3.0, 1.0, E),
                (4.0, 1.0, A2),
                (5.0, 1.0, GS2),
                (6.0, 1.0, E2),
                (7.0, 1.0, E),
            ],
            "verse | A E + D7-D6-A7-E0 fill |",
        )
    )

    rows.append(_eight(25, D, "chorus 8ths D (A-string 5)"))
    rows.append(_eight(26, FS, "chorus 8ths F#m (E-string 2)"))
    rows.append(_eight(27, E, "chorus 8ths E (open 0)"))
    rows.append(_bm_fill_28(28))
    rows.append(_eight(29, D, "chorus 8ths D"))
    rows.append(_eight(30, FS, "chorus 8ths F#m"))
    rows.append(_eight(31, E, "chorus 8ths E"))
    rows.append(
        _hits(
            32,
            [
                (0.0, 1.0, BM),
                (1.0, 1.0, BM),
                (2.0, 1.0, BM),
                (3.0, 1.0, CS),
                (4.0, 1.0, D),
                (5.0, 1.0, D),
                (6.0, 0.5, D),
                (6.5, 0.5, CS),
                (7.0, 1.0, E),
            ],
            "chorus Bm fill 2-2-2-4-5-5 then 16ths 5-4 + E0",
        )
    )

    rows.append(_half_ee(33, FS, D, "inst | F# D | half + two 8ths"))
    rows.append(_half_ee(34, A, E, "inst | A E | half + two 8ths"))
    rows.append(_half_ee(35, FS, D, "inst | F# D | half + two 8ths"))
    rows.append(
        _hits(
            36,
            [
                (0.0, 3.0, A),
                (3.0, 1.0, A),
                (4.0, 1.0, GS2),
                (5.0, 1.0, E2),
                (6.0, 1.0, E),
                (7.0, 1.0, E),
            ],
            "inst | A A + 6-7-0-0 (grace A2 omitted) |",
        )
    )
    rows.append(
        _hits(
            37,
            [
                (0.0, 1.0, FS),
                (1.0, 1.0, FS),
                (2.0, 1.0, FS),
                (4.0, 1.5, D),
                (5.5, 0.5, D),
                (6.0, 1.0, D),
            ],
            "inst m037 F#m|D 8ths then dotted-16-8th D (printed 37)",
        )
    )
    rows.append(
        _hits(
            38,
            [
                (0.0, 1.5, A),
                (1.5, 0.5, A),
                (2.0, 1.0, A),
                (4.0, 0.5, E),
                (4.5, 0.5, E),
                (5.0, 0.5, GS),
                (5.5, 0.5, E),
            ],
            "inst m038 A 5-5-5 then E 0-0-4-0 16ths",
        )
    )
    rows.append(
        _hits(
            39,
            [
                (0.0, 1.0, FS),
                (1.0, 1.0, FS),
                (2.0, 1.0, FS),
                (4.0, 1.5, D),
                (5.5, 0.5, D),
                (6.0, 1.0, D),
            ],
            "inst m039 F#m|D 8ths then dotted-16-8th D",
        )
    )
    rows.append(
        _hits(
            40,
            [
                (0.0, 1.0, A),
                (1.0, 1.0, A),
                (2.0, 1.0, E2),
                (4.0, 2.0, B2),
                (6.0, 1.0, A2),
                (7.0, 1.0, GS2),
            ],
            "inst | A E + D9 quarter then 7-6 (ghost skipped) |",
        )
    )
    rows.append(_whole(41, FS2, "inst m041 F#m|D pedal A-string 9 (printed 41)"))
    rows.append(_pair(42, A, E2, "inst m042 A then E2 (E5 / A7)"))
    rows.append(_whole(43, FS2, "inst F#m|D pedal like 41"))
    rows.append(
        _hits(
            44,
            [
                (0.0, 1.0, A),
                (1.0, 1.0, A),
                (4.0, 1.0, E),
                (5.0, 0.5, A2),
                (5.5, 0.5, E),
                (6.0, 0.5, D),
                (6.5, 0.5, E),
                (7.0, 1.0, E),
            ],
            "inst | A A + E fill 0 / D7 / 0-5-0-0 |",
        )
    )

    # Drive 45–52: two chords per written bar of 8ths (printed 45, 49).
    rows.append(_split8(45, FS, E, "drive m045 F#m|E 2×4 then 0×4"))
    rows.append(_split8(46, A, D, "drive m046 A|D E5 then A5"))
    rows.append(_split8(47, FS, E, "drive m047 F#m|E"))
    rows.append(
        _hits(
            48,
            [
                (0.0, 1.0, BM),
                (1.0, 1.0, BM),
                (2.0, 1.0, BM),
                (3.0, 1.0, BM),
                (4.0, 1.0, BM),
                (5.0, 1.0, D),
                (6.0, 0.5, FS2),
                (6.5, 0.5, G2),
                (7.0, 1.0, D),
            ],
            "drive Bm fill 2×5 + A5 then D-string 4-5-0",
        )
    )
    rows.append(_split8(49, FS, E, "drive m049 F#m|E (printed 49)"))
    rows.append(_split8(50, A, D, "drive m050 A|D"))
    rows.append(_split8(51, FS, E, "drive m051 F#m|E (not Bm)"))
    rows.append(
        _hits(
            52,
            [
                (0.0, 1.0, BM),
                (1.0, 1.0, BM),
                (2.0, 1.0, BM),
                (3.0, 1.0, BM),
                (4.0, 0.5, BM),
                (4.5, 1.5, D3),
                (6.0, 0.5, D3),
                (6.5, 0.5, CS3),
                (7.0, 1.0, D),
            ],
            "drive Bm fill: 2×4, slide A2→D12, 12-11-0 on D",
        )
    )

    # 53–60: still two chords per written bar (printed 53, 57).
    rows.append(_split8(53, FS, GS, "drive m053 F#m|E/G# E-string 2 then 4"))
    rows.append(
        _hits(
            54,
            [
                (0.0, 1.0, A),
                (1.0, 1.0, A),
                (2.0, 1.0, A),
                (3.0, 1.0, E2),
                (4.0, 1.0, E2),
                (5.0, 1.0, D),
                (6.0, 1.0, D),
                (7.0, 1.0, A2),
            ],
            "drive m054 A|D fill 5-5-5-7 | 7-5-5-7",
        )
    )
    rows.append(_split8(55, FS2, E2, "drive m055 F#m|E D4 then A7"))
    rows.append(
        _hits(
            56,
            [
                (0.0, 1.0, BM),
                (1.0, 1.0, B2),
                (2.0, 1.0, BM),
                (3.0, 1.0, E2),
                (4.0, 1.0, B2),
                (5.0, 1.0, BM),
                (6.0, 0.5, A2),
                (6.5, 0.5, GS2),
                (7.0, 1.0, E2),
            ],
            "drive m056 Bm: E7 / D9 slap, end D7-6 A7 (ghosts skipped)",
        )
    )
    rows.append(_split8(57, FS2, GS2, "drive m057 F#m|E/G# A9 then D6 (printed 57)"))
    rows.append(
        _hits(
            58,
            [
                (0.0, 1.0, E2),
                (1.0, 1.0, E2),
                (2.0, 1.0, E2),
                (3.0, 1.0, A2),
                (4.0, 1.0, E2),
                (5.0, 1.0, D),
                (6.0, 1.0, A2),
                (7.0, 1.0, G2),
            ],
            "drive m058 A|E fill A7×3 D7 | A7 A5 D7 D5",
        )
    )
    rows.append(_split8(59, FS2, BM, "drive m059 F#m|E D4 then E-string 7 = B"))
    rows.append(
        _hits(
            60,
            [
                (0.0, 1.0, BM),
                (1.0, 1.0, BM),
                (2.0, 1.0, BM),
                (3.0, 1.0, BM),
                (4.0, 1.0, E2),
                (5.0, 0.5, G2),
                (5.5, 0.5, FS2),
                (6.0, 0.5, D),
                (6.5, 0.5, CS),
                (7.0, 1.0, A),
            ],
            "drive m060 Bm: 7s then D5-4, A5-4-0",
        )
    )

    rows.append(_whole(61, FS, "coda_a F# pedal E-string 2, tied (printed 61)"))
    rows.append(_whole(62, FS, "coda_a F# still tied (TAB 2 from previous)"))
    rows.append(_whole(63, FS, "coda_a F# pedal E-string 2, tied"))
    rows.append(_pair(64, A, E2, "coda_a A then E2 (E5 / A7), section end"))

    rows.append(_whole(65, FS2, "coda_b A-string 9 = F#2 (printed 65)"))
    rows.append(_pair(66, A, E2, "coda_b A then E2 (E5 / A7)"))
    rows.append(_whole(67, FS2, "coda_b A-string 9 = F#2"))
    rows.append(_pair(68, A, E2, "coda_b E5 then A7"))
    rows.append(_whole(69, FS2, "coda_b A-string 9 = F#2 (printed 69)"))
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
    13: ("half_ee", (FS, D)),
    14: ("half_ee", (A, E)),
    15: ("half_ee", (FS, D)),
    16: ("hits", (A, A2, GS2, E2, E)),
    17: ("half_ee", (FS, D)),
    18: ("half_ee", (A, E)),
    24: ("hits", (A, E, A2, GS2, E2, E)),
    25: ("eight", (D,)),
    26: ("eight", (FS,)),
    27: ("eight", (E,)),
    28: ("hits", (BM, BM, BM, BM, BM, BM, D, CS)),
    29: ("eight", (D,)),
    32: ("hits", (BM, BM, BM, CS, D, D, D, CS, E)),
    33: ("half_ee", (FS, D)),
    34: ("half_ee", (A, E)),
    36: ("hits", (A, A, GS2, E2, E, E)),
    37: ("hits", (FS, FS, FS, D, D, D)),
    38: ("hits", (A, A, A, E, E, GS, E)),
    39: ("hits", (FS, FS, FS, D, D, D)),
    40: ("hits", (A, A, E2, B2, A2, GS2)),
    41: ("whole", (FS2,)),
    42: ("pair", (A, E2)),
    44: ("hits", (A, A, E, A2, E, D, E, E)),
    45: ("split8", (FS, E)),
    46: ("split8", (A, D)),
    47: ("split8", (FS, E)),
    48: ("hits", (BM, BM, BM, BM, BM, D, FS2, G2, D)),
    49: ("split8", (FS, E)),
    51: ("split8", (FS, E)),
    52: ("hits", (BM, BM, BM, BM, BM, D3, D3, CS3, D)),
    53: ("split8", (FS, GS)),
    54: ("hits", (A, A, A, E2, E2, D, D, A2)),
    55: ("split8", (FS2, E2)),
    56: ("hits", (BM, B2, BM, E2, B2, BM, A2, GS2, E2)),
    57: ("split8", (FS2, GS2)),
    58: ("hits", (E2, E2, E2, A2, E2, D, A2, G2)),
    59: ("split8", (FS2, BM)),
    60: ("hits", (BM, BM, BM, BM, E2, G2, FS2, D, CS, A)),
    61: ("whole", (FS,)),
    62: ("whole", (FS,)),
    63: ("whole", (FS,)),
    64: ("pair", (A, E2)),
    65: ("whole", (FS2,)),
    66: ("pair", (A, E2)),
    67: ("whole", (FS2,)),
    68: ("pair", (A, E2)),
    69: ("whole", (FS2,)),
    70: ("pair", (A, E2)),
    71: ("whole", (FS,)),
    72: ("pair", (A, E)),
}
