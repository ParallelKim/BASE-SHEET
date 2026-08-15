"""Antifreeze bass chart: one row per written bar (akbobada, 5 pages).

MIDI: B1=35 C#2=37 F#1=30 E1=28 A#1=34 G#1=32 D#2=39 E2=40 A2=45 G#2=44.
PLAY is 1-based written bars in performance order (print repeats + voltas).
"""

from chart_table import BarSpec

B, CS, FS, EN, AS, GS, DS = 35, 37, 30, 28, 34, 32, 39


def _eight(w: int, p: int, comment: str, lock: str = "score") -> BarSpec:
    return BarSpec(w, "eight", (p,), lock, comment)


def _whole(w: int, p: int, comment: str) -> BarSpec:
    return BarSpec(w, "whole", (p,), "score", comment)


def _hits(w: int, events: list[tuple[float, float, int]], comment: str) -> BarSpec:
    ev = tuple((float(e), float(d), int(p)) for e, d, p in events)
    return BarSpec(w, "hits", tuple(p for _, _, p in ev), "score", comment, events=ev)


def _first_n_eights(w: int, n: int, pitch: int, comment: str) -> BarSpec:
    events = [(float(i), 1.0, pitch) for i in range(n)]
    return _hits(w, events, comment)


def _bars() -> list[BarSpec]:
    rows: list[BarSpec] = []

    def add_eights(start: int, pitches: list[int], comment: str) -> None:
        for i, p in enumerate(pitches):
            rows.append(_eight(start + i, p, comment))

    add_eights(1, [B, CS, FS, EN] * 2, "p.1 intro | B | C#7 | F# | E |")
    add_eights(9, [B, CS, FS, EN] * 2, "p.1 verse, same riff")
    add_eights(17, [B, CS, AS, B], "p.2 mm.17–20")
    add_eights(21, [GS, CS, FS, FS], "p.2 mm.21–24")
    add_eights(25, [DS, CS, B, FS], "p.2 mm.25–28")
    add_eights(29, [DS, CS, B, FS], "p.2 mm.29–32")
    add_eights(33, [B, AS, B, AS, B, AS, B], "p.3 vamp B / A#m7 (A-string 2 / 1)")
    rows.append(_eight(40, GS, "1st ending G#m7 E-string 4"))
    rows.append(_eight(41, FS, "1st ending F# E-string 2"))
    rows.append(_eight(42, FS, "1st ending last bar F# 8ths (TAB 2s)"))
    rows.append(_eight(43, GS, "2nd ending G#m7 E-string 4"))
    add_eights(44, [FS, FS, FS, FS], "p.4 F# pedal (printed 44 = E-string 2)")
    add_eights(48, [DS, GS, CS, FS] * 3, "chorus loop | D#m | G# | C#7 | F# |")

    # p.5 mm.60–63: main staff is straight 8ths (fill staff below is optional).
    add_eights(60, [DS, GS, CS, FS], "p.5 loop | D#m | G# | C#7 | F# |")

    # 64: 2nd ending F# fill — two C# 8ths then A-string 6-4-6-4-6-4.
    rows.append(
        _hits(
            64,
            [
                (0.0, 1.0, CS),
                (1.0, 1.0, CS),
                (2.0, 1.0, DS),
                (3.0, 1.0, CS),
                (4.0, 1.0, DS),
                (5.0, 1.0, CS),
                (6.0, 1.0, DS),
                (7.0, 1.0, CS),
            ],
            "p.5 m064 2nd ending fill A4-4-6-4-6-4-6-4",
        )
    )
    rows.append(_first_n_eights(65, 2, DS, "p.5 D#m: two 8ths then rest"))
    rows.append(_first_n_eights(66, 4, GS, "p.5 G#: four 8ths then rest"))
    rows.append(_first_n_eights(67, 2, CS, "p.5 C#7: two 8ths then rest"))
    rows.append(_first_n_eights(68, 4, FS, "p.5 F#: four 8ths then rest"))
    rows.append(
        _hits(
            69,
            [(0.0, 1.0, DS), (1.0, 1.0, DS), (7.0, 1.0, GS)],
            "p.5 D#m: two 8ths, rest, G# pickup 8th",
        )
    )
    rows.append(_first_n_eights(70, 4, GS, "p.5 G#: four 8ths then rest"))
    rows.append(_first_n_eights(71, 2, CS, "p.5 C#7: two 8ths then rest"))
    rows.append(_first_n_eights(72, 4, FS, "p.5 F#: four 8ths then rest"))
    rows.append(_whole(73, DS, "p.5 outro whole D#m"))
    rows.append(_whole(74, GS, "p.5 outro whole G#"))
    rows.append(_whole(75, CS, "p.5 outro whole C#7"))
    rows.append(_whole(76, FS, "p.5 outro whole F#"))
    rows.append(_whole(77, DS, "p.5 outro whole D#m"))
    rows.append(_whole(78, GS, "p.5 outro whole G#"))
    rows.append(_whole(79, CS, "p.5 outro whole C#7"))
    rows.append(_whole(80, FS, "p.5 final whole F# (volta endings both F#)"))
    return rows


BARS = _bars()

# 1-based written order as performed on Antifreeze_bass_mixed.m4a.
# Print: |: 9–24 :|, |: 25–42 1st / 25–39+43 2nd, chorus 48–59 ×2,
# outro |: 73–80 :|. p.5 mm.60–64 (fill ending) is not a separate take
# on this mix — those roots already occur in the double chorus; the
# tape goes to the 65 breakdown. BarSpecs 60–64 stay as print truth.
PLAY = (
    list(range(1, 9))
    + list(range(9, 25))
    + list(range(9, 25))  # |: m.9  :| m.24
    + list(range(25, 43))  # |: m.25 through 1st ending 42
    + list(range(25, 40))
    + [43]  # 2nd time: 25–39 + 2nd ending
    + list(range(44, 48))  # pedal once
    + list(range(48, 60))
    + list(range(48, 60))  # chorus loop 2x (six D#–G#–C#–F# cycles)
    + list(range(65, 73))  # breakdown; skip 60–64 on this mix
    + list(range(73, 81))
    + list(range(73, 81))  # |: 73–80 :| both endings F#
)

SECTIONS = {
    "intro": (0, 8),
    "verse": (8, 16),
    "middle_a": (16, 40),  # 17–24 + 9–24 repeat
    "middle_b": (40, 48),  # first 25–32 (D# C# B F#)
    "vamp": (48, 74),  # 33–42 + 25–32 + 33–39+43
    "pedal": (74, 78),
    "chorus": (78, 102),
    "late": (102, 200),
}

LOCK_SNAPSHOT: dict[int, tuple[str, tuple[int, ...]]] = {
    1: ("eight", (B,)),
    2: ("eight", (CS,)),
    3: ("eight", (FS,)),
    4: ("eight", (EN,)),
    9: ("eight", (B,)),
    17: ("eight", (B,)),
    18: ("eight", (CS,)),
    19: ("eight", (AS,)),
    20: ("eight", (B,)),
    21: ("eight", (GS,)),
    25: ("eight", (DS,)),
    33: ("eight", (B,)),
    34: ("eight", (AS,)),
    40: ("eight", (GS,)),
    41: ("eight", (FS,)),
    42: ("eight", (FS,)),
    43: ("eight", (GS,)),
    44: ("eight", (FS,)),
    48: ("eight", (DS,)),
    49: ("eight", (GS,)),
    50: ("eight", (CS,)),
    51: ("eight", (FS,)),
    60: ("eight", (DS,)),
    61: ("eight", (GS,)),
    62: ("eight", (CS,)),
    63: ("eight", (FS,)),
    64: ("hits", (CS, CS, DS, CS, DS, CS, DS, CS)),
    65: ("hits", (DS, DS)),
    66: ("hits", (GS, GS, GS, GS)),
    67: ("hits", (CS, CS)),
    68: ("hits", (FS, FS, FS, FS)),
    69: ("hits", (DS, DS, GS)),
    70: ("hits", (GS, GS, GS, GS)),
    71: ("hits", (CS, CS)),
    72: ("hits", (FS, FS, FS, FS)),
    73: ("whole", (DS,)),
    74: ("whole", (GS,)),
    75: ("whole", (CS,)),
    76: ("whole", (FS,)),
    77: ("whole", (DS,)),
    78: ("whole", (GS,)),
    79: ("whole", (CS,)),
    80: ("whole", (FS,)),
}

PLAY_SNAPSHOT_PREFIX = (
    list(range(1, 9)) + list(range(9, 25)) * 2 + list(range(25, 43))
)
PLAY_SNAPSHOT_VOLTA2 = list(range(33, 40)) + [43]
