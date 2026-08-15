"""Antifreeze bass chart: one row per written bar (akbobada, 5 pages).

MIDI: B1=35 C#2=37 F#1=30 E1=28 A#1=34 G#1=32 D#2=39.
PLAY is 1-based written bars in performance order (voltas + chorus 2x).
"""

from chart_table import BarSpec

B, CS, FS, EN, AS, GS, DS = 35, 37, 30, 28, 34, 32, 39


def _eight(w: int, p: int, comment: str, lock: str = "score") -> BarSpec:
    return BarSpec(w, "eight", (p,), lock, comment)


def _skip(w: int, comment: str) -> BarSpec:
    return BarSpec(w, "skip", (), "approx", comment)


def _bars() -> list[BarSpec]:
    rows: list[BarSpec] = []

    def add_eights(start: int, pitches: list[int], comment: str, lock: str = "score") -> None:
        for i, p in enumerate(pitches):
            rows.append(_eight(start + i, p, comment, lock))

    add_eights(1, [B, CS, FS, EN] * 2, "p.1 intro | B | C#7 | F# | E |")
    add_eights(9, [B, CS, FS, EN] * 2, "p.1 verse, same riff")
    add_eights(17, [B, CS, AS, B], "p.2 mm.17–20")
    add_eights(21, [GS, CS, FS, FS], "p.2 mm.21–24")
    add_eights(25, [DS, CS, B, FS], "p.2 mm.25–28")
    add_eights(29, [DS, CS, B, FS], "p.2 mm.29–32")
    add_eights(33, [B, AS, B, AS, B, AS, B], "p.3 vamp B / A#m7")
    rows.append(_eight(40, GS, "1st ending G#m7"))
    rows.append(_eight(41, FS, "1st ending F#"))
    rows.append(_skip(42, "1st ending last bar not locked — not scored"))
    rows.append(_eight(43, GS, "2nd ending G#m7"))
    add_eights(44, [FS, FS, FS, FS], "p.4 F# pedal")
    add_eights(48, [DS, GS, CS, FS] * 3, "chorus loop | D#m | G# | C#7 | F# |")
    for w in range(60, 81):
        rows.append(_skip(w, "p.5 fills/outro not locked — not scored"))
    return rows


BARS = _bars()

# 1-based written order as performed.
PLAY = (
    list(range(1, 33))
    + list(range(33, 43))  # 33–42 first ending
    + list(range(33, 40))
    + [43]  # 33–39 + 2nd ending
    + list(range(44, 48))  # pedal once
    + list(range(48, 60))
    + list(range(48, 60))  # chorus loop 2x
    + list(range(60, 81))
)

SECTIONS = {
    "intro": (0, 8),
    "verse": (8, 16),
    "middle_a": (16, 24),
    "middle_b": (24, 32),
    "vamp": (32, 50),
    "pedal": (50, 54),
    "chorus": (54, 78),
    "late": (78, 200),
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
    43: ("eight", (GS,)),
    44: ("eight", (FS,)),
    48: ("eight", (DS,)),
    49: ("eight", (GS,)),
    50: ("eight", (CS,)),
    51: ("eight", (FS,)),
}

PLAY_SNAPSHOT_PREFIX = list(range(1, 33)) + list(range(33, 43))
PLAY_SNAPSHOT_VOLTA2 = list(range(33, 40)) + [43]
