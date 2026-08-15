"""Published 검정치마 「Antifreeze」 bass tab (akbobada): q=128, 4/4.

Bass is almost all root-position 8ths. Page 1 is 4 sharps on the print;
later pages add A#. MIDI uses bass-register roots (E1=28).

Volta: mm.40–42 1st ending, m.43 2nd ending. Chorus loop mm.48–59 is
played twice. From m.60 the print is fills/syncopation — those bars are
scored as one root per bar so 8th-grid density is not pretended.
"""

from sheet_score import Hit, bar8, expand_play_order, sustain

SCORE_BPM = 128.0
SCORE_KEY = "F#"

# A-string 2/4/1/6 = B / C# / A# / D#; E-string 2/4/0 = F# / G# / E
B, CS, FS, EN = 35, 37, 30, 28
AS, GS, DS = 34, 32, 39

INTRO_BAR_ROOTS = [B, CS, FS, EN] * 4


def _eighth_bars(*pitches: int, start: int = 0) -> list[list[Hit]]:
    return [bar8(p, start + i) for i, p in enumerate(pitches)]


def _root_bars(*pitches: int, start: int = 0) -> list[list[Hit]]:
    """One downbeat sample per bar — for fills that are not straight 8ths."""
    return [[sustain(p, start + i, 0.0, 8.0)] for i, p in enumerate(pitches)]


def written_bars() -> list[list[Hit]]:
    bars: list[list[Hit]] = []

    def add(*pitches: int) -> None:
        bars.extend(_eighth_bars(*pitches, start=len(bars)))

    def add_roots(*pitches: int) -> None:
        bars.extend(_root_bars(*pitches, start=len(bars)))

    # p.1 mm.1–8 intro | B | C#7 | F# | E | ×2
    add(*[B, CS, FS, EN] * 2)
    # p.1 mm.9–16 verse: same riff
    add(*[B, CS, FS, EN] * 2)
    # p.2 mm.17–32
    add(B, CS, AS, B)  # 17–20
    add(GS, CS, FS, FS)  # 21–24
    add(DS, CS, B, FS)  # 25–28
    add(DS, CS, B, FS)  # 29–32
    # p.3 mm.33–39 B / A#m7 vamp
    add(B, AS, B, AS, B, AS, B)
    # mm.40–42 first ending G#m7 | F# | F#
    add(GS, FS, FS)
    # m.43 second ending G#m7
    add(GS)
    # p.4 mm.44–47 F# pedal 8ths
    add(FS, FS, FS, FS)
    # mm.48–59 | D#m | G# | C#7 | F# | ×3
    add(*[DS, GS, CS, FS] * 3)
    # p.5 mm.60–72 fills: roots only (print is slides / syncopation / 1st ending)
    add_roots(DS, GS, CS, FS)  # 60–63
    add_roots(DS, GS, CS, FS, DS)  # 64–68
    add_roots(GS, CS, FS, DS)  # 69–72
    # mm.73–80 outro wholes | D#m | G# | C#7 | F# | ×2
    add_roots(*[DS, GS, CS, FS] * 2)
    return bars


def play_order(n_written: int) -> list[int]:
    """Performance order: 1st ending, 2nd ending, chorus loop twice."""
    play = list(range(0, 32))
    play += list(range(32, 42))  # mm.33–42 first ending
    play += list(range(32, 39)) + [42]  # mm.33–39 + m.43
    play += list(range(43, 47))  # mm.44–47 pedal once
    play += list(range(47, 59))  # mm.48–59
    play += list(range(47, 59))  # 2x chorus loop
    play += list(range(59, n_written))  # mm.60–end
    return play


def played_hits() -> list[Hit]:
    w = written_bars()
    return expand_play_order(w, play_order(len(w)))


def n_played_bars() -> int:
    return len(play_order(len(written_bars())))


# Played-bar indices. Names follow the print, not one blended chart.
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
