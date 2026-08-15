"""Published 자우림 「잊지」 bass tab (akbobada): q≈83, F# minor, 4/4.

Bars 1–12 tacet. Verse 13–24 cycles F#m / D / A / E roots.
Do not commit the stem; copy to tests/fixtures/ijji_bass.m4a locally.
"""

SCORE_BPM = 84.0
SCORE_KEY = "F# minor"
TACET_BARS = 12
# One bar each: F#1, D2, A1, E1 (MIDI), repeated through bars 13–24.
VERSE_BAR_ROOTS = [30, 38, 33, 28] * 3
# Chorus 25–28 bar roots: D / F#m / E / Bm
CHORUS_BAR_ROOTS = [38, 30, 28, 35]
