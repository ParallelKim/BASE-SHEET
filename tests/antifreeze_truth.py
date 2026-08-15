"""Published 검정치마 「Antifreeze」 bass tab (akbobada): q=128, B / F# 영역, 4/4.

Open-string MIDI: E1=28, A1=33. Hits are 8th-note roots except the
outro whole notes. Fills at section ends are scored as the bar's root
(chroma still counts; exact may miss). Repeat/1st–2nd endings are
expanded in ``PLAY_ORDER``.
"""

from sheet_score import Hit, bar8, expand_play_order, sustain

SCORE_BPM = 128.0
SCORE_KEY = "F#"

# A-string 2/4/1/6 = B / C# / A# / D#; E-string 2/4/0 = F# / G# / E
B, CS, FS, EN = 35, 37, 30, 28
AS, GS, DS = 34, 32, 39

# Kept for the original intro-only test.
INTRO_BAR_ROOTS = [B, CS, FS, EN] * 4


def _eighth_bars(*pitches: int, start: int = 0) -> list[list[Hit]]:
    return [bar8(p, start + i) for i, p in enumerate(pitches)]


def written_bars() -> list[list[Hit]]:
    bars: list[list[Hit]] = []

    def add(*pitches: int) -> None:
        bars.extend(_eighth_bars(*pitches, start=len(bars)))

    # p.1 mm.1–16 intro + verse: | B | C#7 | F# | E | ×4
    add(*[B, CS, FS, EN] * 4)
    # p.2 mm.17–32
    add(B, CS, AS, B)  # 17–20
    add(GS, CS, FS, FS)  # 21–24
    add(DS, CS, B, FS)  # 25–28
    add(DS, CS, B, FS)  # 29–32
    # p.3 mm.33–41 first ending (B / A#m7 vamp → G#m7 | F#)
    add(B, AS, B, AS, B, AS, B, GS, FS)
    # m.43 second ending G#m7 (written after the repeat mark)
    add(GS)
    # p.4 mm.44–47 F# pedal
    add(FS, FS, FS, FS)
    # mm.48–59 | D#m | G# | C#7 | F# | ×3
    add(*[DS, GS, CS, FS] * 3)
    # p.5 mm.60–63 same loop (fill approximated as roots)
    add(DS, GS, CS, FS)
    # mm.64–68 fill / bridge, still the loop plus one extra D#m
    add(DS, GS, CS, FS, DS)
    # mm.69–72 rhythmic variation, same roots
    add(GS, CS, FS, DS)
    # mm.73–80 outro whole notes | D#m | G# | C#7 | F# | ×2
    n = len(bars)
    for i, p in enumerate([DS, GS, CS, FS] * 2):
        bars.append([sustain(p, n + i, 0.0, 8.0)])
    return bars


def played_hits() -> list[Hit]:
    """Performance order: 1st ending, then 2nd ending, chorus repeated."""
    w = written_bars()
    # 0–31 mm.1–32; 32–40 mm.33–41; 41 m.43 2nd ending; 42+ rest of chart
    play = list(range(0, 32))
    play += list(range(32, 41))  # first ending
    play += list(range(32, 39)) + [41]  # 33–39 + 2nd ending
    play += list(range(42, 58))  # mm.44–59
    play += list(range(42, 58))  # repeat chorus
    play += list(range(58, len(w)))
    return expand_play_order(w, play)


SECTIONS = {
    "intro": (0, 16),  # played-bar indices
    "middle": (16, 32),
    "vamp": (32, 50),
    "chorus": (50, 82),
    "outro": (82, 200),
}
