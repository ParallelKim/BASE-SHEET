"""Fast checks: published-tab truth matches the print's bar math.

These do not run transcription. If they fail, slow song tests are scoring
the wrong chart and must not be used as pipeline evidence.
"""

from antifreeze_truth import (
    INTRO_BAR_ROOTS,
    SECTIONS as AF_SECTIONS,
    n_played_bars,
    play_order,
    played_hits as af_hits,
    written_bars,
)
from ijji_truth import N_BARS, SECTIONS as IJ_SECTIONS, TACET_BARS, played_hits as ij_hits
from song_score import hits_in_bars


def _assert_partition(sections: dict[str, tuple[int, int]], n_bars: int, start: int = 0) -> None:
    items = sorted(sections.items(), key=lambda kv: kv[1][0])
    assert items[0][1][0] == start, items[0]
    prev = start
    for name, (a, b) in items:
        assert a == prev, f"{name} expected start {prev}, got {a}"
        assert b > a, name
        prev = b
    last = items[-1][1][1]
    assert last >= n_bars, f"last section ends at {last}, chart has {n_bars} bars"


def test_antifreeze_written_and_play_order():
    w = written_bars()
    assert len(w) == 80  # mm.1–80
    assert [h.pitch for h in w[0]] == [INTRO_BAR_ROOTS[0]] * 8
    # First ending is G#m7 | F# | F# (mm.40–42), 2nd ending is G#m7 (m.43).
    assert [h.pitch for h in w[39]] == [32] * 8  # m.40 G#
    assert [h.pitch for h in w[40]] == [30] * 8
    assert [h.pitch for h in w[41]] == [30] * 8
    assert [h.pitch for h in w[42]] == [32] * 8  # m.43
    order = play_order(len(w))
    assert order.count(42) == 1  # 2nd ending once
    assert order.count(41) == 1  # last bar of 1st ending only on first pass
    assert order[32:42] == list(range(32, 42))
    assert order[42:50] == list(range(32, 39)) + [42]


def test_antifreeze_sections_partition_played_bars():
    hits = af_hits()
    n = n_played_bars()
    assert max(h.bar for h in hits) + 1 == n
    _assert_partition(AF_SECTIONS, n, start=0)
    # Intro vs verse are the same riff but different time — keep them split.
    intro = hits_in_bars(hits, *AF_SECTIONS["intro"])
    verse = hits_in_bars(hits, *AF_SECTIONS["verse"])
    assert len(intro) == 8 * 8
    assert [h.pitch for h in intro[:8]] == [h.pitch for h in verse[:8]]
    # Chorus loop is 8ths; late (fills/outro) is one root per bar.
    chorus = hits_in_bars(hits, *AF_SECTIONS["chorus"])
    late = hits_in_bars(hits, *AF_SECTIONS["late"])
    assert all(h.dur_eighths == 1.0 for h in chorus)
    assert all(h.dur_eighths == 8.0 for h in late)
    assert sum(len(hits_in_bars(hits, a, b)) for a, b in AF_SECTIONS.values()) == len(hits)


def test_ijji_tacet_then_two_roots_per_verse_bar():
    hits = ij_hits()
    assert max(h.bar for h in hits) + 1 == N_BARS
    assert all(h.bar >= TACET_BARS for h in hits)
    verse = hits_in_bars(hits, *IJ_SECTIONS["verse"])
    assert len(verse) == 24  # 12 bars × 2 halves
    # mm.13–14 = bars 12–13: | F# D | A E |
    assert [(h.eighth, h.pitch) for h in verse[:4]] == [
        (0.0, 30),
        (4.0, 38),
        (0.0, 33),
        (4.0, 28),
    ]


def test_ijji_chorus_is_one_chord_eighths():
    hits = ij_hits()
    chorus = hits_in_bars(hits, *IJ_SECTIONS["chorus"])
    assert len(chorus) == 8 * 8
    assert chorus[0].pitch == 38 and chorus[8].pitch == 30
    assert chorus[16].pitch == 28 and chorus[24].pitch == 35


def test_ijji_sections_partition_and_tacet_is_empty():
    hits = ij_hits()
    _assert_partition(IJ_SECTIONS, N_BARS, start=0)
    assert hits_in_bars(hits, *IJ_SECTIONS["tacet"]) == []
    sounding = [h for h in hits]
    assert sum(len(hits_in_bars(hits, a, b)) for a, b in IJ_SECTIONS.values()) == len(sounding)
    coda_a = hits_in_bars(hits, *IJ_SECTIONS["coda_a"])
    assert coda_a[0].pitch == 30
    assert coda_a[-1].pitch == 33
