"""Antifreeze bass chart: one row per written bar (akbobada, 5 pages).

MIDI: B1=35 C#2=37 F#1=30 E1=28 A#1=34 G#1=32 D#2=39 E2=40 A2=45.
PLAY is 1-based written bars in performance order (voltas + chorus 2x).
"""

from chart_table import BarSpec

B, CS, FS, EN, AS, GS, DS = 35, 37, 30, 28, 34, 32, 39
E2, A2 = 40, 45


def _eight(w: int, p: int, comment: str, lock: str = "score") -> BarSpec:
    return BarSpec(w, "eight", (p,), lock, comment)


def _skip(w: int, comment: str) -> BarSpec:
    return BarSpec(w, "skip", (), "approx", comment)


def _hits(w: int, events: list[tuple[float, float, int]], comment: str) -> BarSpec:
    ev = tuple((float(e), float(d), int(p)) for e, d, p in events)
    return BarSpec(w, "hits", tuple(p for _, _, p in ev), "score", comment, events=ev)


def _eights_from_frets(w: int, frets: list[int], fmap: dict[int, int], comment: str) -> BarSpec:
    """One printed TAB digit per eighth; remaining eighths are omitted."""
    events = []
    for i, f in enumerate(frets):
        if f not in fmap:
            continue
        events.append((float(i), 1.0, fmap[f]))
    assert events, (w, frets)
    return _hits(w, events, comment)


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
    rows.append(_eight(42, FS, "1st ending last bar F# 8ths (TAB 2s)"))
    rows.append(_eight(43, GS, "2nd ending G#m7"))
    add_eights(44, [FS, FS, FS, FS], "p.4 F# pedal")
    add_eights(48, [DS, GS, CS, FS] * 3, "chorus loop | D#m | G# | C#7 | F# |")

    # p.5 mm.60–80: another D# G# C# F# cycle; some bars are fills.
    loop = [DS, GS, CS, FS]
    # 60–63: TAB 6/4/beams/2 = straight loop
    add_eights(60, loop, "p.5 loop | D#m | G# | C#7 | F# |")

    # 64 DS fill: TAB 6-8-6-6
    rows.append(
        _eights_from_frets(64, [6, 8, 6, 6], {6: DS, 8: E2}, "p.5 D# fill 6-8-6-6")
    )
    # 65 GS fill: TAB 8-6-4-6-4-4-4 (drop OCR '3')
    rows.append(
        _eights_from_frets(
            65, [8, 6, 4, 6, 4, 4, 4], {8: E2, 6: DS, 4: GS}, "p.5 G# fill"
        )
    )
    # 66 CS fill: TAB 6-8-8-6-4-4
    rows.append(
        _eights_from_frets(
            66, [6, 8, 8, 6, 4, 4], {6: DS, 8: E2, 4: CS}, "p.5 C# fill"
        )
    )
    rows.append(_skip(67, "p.5 TAB not locked"))
    # 68 DS fill: TAB 4-4-6-4-6-4-6-4
    rows.append(
        _eights_from_frets(
            68, [4, 4, 6, 4, 6, 4, 6, 4], {4: GS, 6: DS}, "p.5 D#/G# fill 4-6"
        )
    )
    rows.append(_skip(69, "p.5 TAB not locked"))
    rows.append(_eight(70, CS, "p.5 C# 8ths (TAB 4s)"))
    rows.append(_skip(71, "p.5 TAB not locked"))
    rows.append(_skip(72, "p.5 TAB not locked"))
    rows.append(_eight(73, GS, "p.5 G# 8ths (TAB 4s)"))
    rows.append(_skip(74, "p.5 TAB not locked"))
    rows.append(_eight(75, FS, "p.5 F# 8ths (TAB 2s)"))
    for w in (76, 77, 78):
        rows.append(_skip(w, "p.5 TAB not locked"))
    rows.append(
        _hits(
            79,
            [(0.0, 2.0, EN), (2.0, 2.0, EN), (4.0, 4.0, FS)],
            "p.5 outro 0-0-2",
        )
    )
    rows.append(_skip(80, "p.5 final bar TAB not locked"))
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
    64: ("hits", (DS, E2, DS, DS)),
    65: ("hits", (E2, DS, GS, DS, GS, GS, GS)),
    66: ("hits", (DS, E2, E2, DS, CS, CS)),
    68: ("hits", (GS, GS, DS, GS, DS, GS, DS, GS)),
    70: ("eight", (CS,)),
    73: ("eight", (GS,)),
    75: ("eight", (FS,)),
    79: ("hits", (EN, EN, FS)),
}

PLAY_SNAPSHOT_PREFIX = list(range(1, 33)) + list(range(33, 43))
PLAY_SNAPSHOT_VOLTA2 = list(range(33, 40)) + [43]
