"""Chart table is the print concordance. Truth must expand it; snapshots freeze locked bars."""

from antifreeze_chart import (
    BARS as AF_BARS,
    LOCK_SNAPSHOT as AF_LOCK,
    PLAY as AF_PLAY,
    PLAY_SNAPSHOT_PREFIX,
    PLAY_SNAPSHOT_VOLTA2,
    SECTIONS as AF_SECTIONS,
)
from antifreeze_truth import (
    INTRO_BAR_ROOTS,
    n_played_bars,
    play_order,
    played_hits as af_hits,
    written_bars,
)
from chart_table import require_contiguous, spec_hits
from ijji_chart import BARS as IJ_BARS, LOCK_SNAPSHOT as IJ_LOCK, PLAY as IJ_PLAY, SECTIONS as IJ_SECTIONS
from ijji_truth import N_BARS, TACET_BARS, played_hits as ij_hits
from song_score import hits_in_bars


def _assert_partition(sections: dict[str, tuple[int, int]], n_bars: int, start: int = 0) -> None:
    items = sorted(sections.items(), key=lambda kv: kv[1][0])
    assert items[0][1][0] == start, items[0]
    prev = start
    for name, (a, b) in items:
        assert a == prev, f"{name} expected start {prev}, got {a}"
        assert b > a, name
        prev = b
    assert items[-1][1][1] >= n_bars


def _assert_snapshot(bars, snap: dict) -> None:
    by_w = {s.written: s for s in bars}
    for w, (rhythm, pitches) in snap.items():
        spec = by_w[w]
        assert spec.lock == "score", f"snapshot bar {w} must be lock=score, got {spec.lock}"
        assert spec.rhythm == rhythm, (w, spec.rhythm, rhythm)
        assert spec.pitches == pitches, (w, spec.pitches, pitches)


def test_ijji_chart_is_72_contiguous_bars():
    require_contiguous(IJ_BARS)
    assert len(IJ_BARS) == N_BARS == 72
    assert IJ_PLAY == list(range(1, 73))
    assert IJ_BARS[0].rhythm == "rest"
    assert all(s.rhythm == "rest" for s in IJ_BARS[:TACET_BARS])


def test_ijji_lock_snapshot_matches_print_reads():
    _assert_snapshot(IJ_BARS, IJ_LOCK)


def test_ijji_truth_is_exactly_the_chart():
    from chart_table import played_from_specs

    assert ij_hits() == played_from_specs(IJ_BARS, IJ_PLAY)


def test_ijji_verse_two_roots_per_bar():
    hits = ij_hits()
    verse = hits_in_bars(hits, *IJ_SECTIONS["verse"])
    assert len(verse) == 31  # 10 pair bars + mm.16/24 fills
    assert [(h.eighth, h.pitch) for h in verse[:4]] == [
        (0.0, 30),
        (4.0, 38),
        (0.0, 33),
        (4.0, 28),
    ]


def test_ijji_chorus_one_chord_eighths():
    chorus = hits_in_bars(ij_hits(), *IJ_SECTIONS["chorus"])
    assert len(chorus) == 64  # 6 eight-bars + two Bm fills
    assert chorus[0].pitch == 38 and chorus[8].pitch == 30


def test_ijji_fill_bar_16_is_a_then_lick():
    spec = IJ_BARS[15]
    assert spec.lock == "score" and spec.rhythm == "hits"
    assert spec.pitches[0] == 33 and spec.pitches[-1] == 28


def test_ijji_sections_partition():
    hits = ij_hits()
    _assert_partition(IJ_SECTIONS, N_BARS, start=0)
    assert hits_in_bars(hits, *IJ_SECTIONS["tacet"]) == []
    coda_b = hits_in_bars(hits, *IJ_SECTIONS["coda_b"])
    assert len(coda_b) == 12
    assert coda_b[0].pitch == 42  # A-string 9 = F#2
    assert sum(len(hits_in_bars(hits, a, b)) for a, b in IJ_SECTIONS.values()) == len(hits)


def test_ijji_all_written_bars_are_score_locked():
    approx = [s for s in IJ_BARS if s.lock == "approx"]
    assert approx == []
    assert all(s.lock == "score" for s in IJ_BARS)


def test_hits_rhythm_expands_onsets():
    spec = IJ_BARS[15]  # m.16 fill
    hits = spec_hits(spec, 15)
    assert [h.pitch for h in hits] == list(spec.pitches)
    assert hits[0].eighth == 0.0
    assert sum(h.dur_eighths for h in hits) == 8.0


def test_antifreeze_chart_is_80_written_bars():
    require_contiguous(AF_BARS)
    assert len(AF_BARS) == 80
    assert len(AF_PLAY) == n_played_bars() == 99
    assert [h.pitch for h in written_bars()[0]] == [INTRO_BAR_ROOTS[0]] * 8


def test_antifreeze_lock_snapshot_matches_print_reads():
    _assert_snapshot(AF_BARS, AF_LOCK)


def test_antifreeze_play_order_voltas_frozen():
    assert AF_PLAY[:42] == PLAY_SNAPSHOT_PREFIX
    i = AF_PLAY.index(43)
    assert AF_PLAY[i - 7 : i + 1] == PLAY_SNAPSHOT_VOLTA2
    assert AF_PLAY.count(43) == 1
    assert AF_PLAY.count(48) == 2  # chorus loop twice
    assert play_order(80) == [w - 1 for w in AF_PLAY]


def test_antifreeze_truth_is_exactly_the_chart():
    from chart_table import played_from_specs

    assert af_hits() == played_from_specs(AF_BARS, AF_PLAY)


def test_antifreeze_sections_partition_played_bars():
    hits = af_hits()
    n = n_played_bars()
    assert n == 99
    _assert_partition(AF_SECTIONS, n, start=0)
    intro = hits_in_bars(hits, *AF_SECTIONS["intro"])
    verse = hits_in_bars(hits, *AF_SECTIONS["verse"])
    assert len(intro) == 64
    assert [h.pitch for h in intro[:8]] == [h.pitch for h in verse[:8]]
    chorus = hits_in_bars(hits, *AF_SECTIONS["chorus"])
    late = hits_in_bars(hits, *AF_SECTIONS["late"])
    assert all(h.dur_eighths == 1.0 for h in chorus)
    assert len(late) == 84
    vamp = hits_in_bars(hits, *AF_SECTIONS["vamp"])
    assert len(vamp) == 144  # includes 1st-ending m.42 F# 8ths


def test_antifreeze_approx_bars_are_unread_p5_only():
    approx = [s for s in AF_BARS if s.lock == "approx"]
    assert [s.written for s in approx] == [67, 69, 71, 72, 74, 76, 77, 78, 80]
    assert all(s.rhythm == "skip" and s.pitches == () for s in approx)


def test_antifreeze_bar_42_and_p5_loop_are_score_locked():
    by_w = {s.written: s for s in AF_BARS}
    assert by_w[42].lock == "score" and by_w[42].pitches == (30,)
    assert by_w[60].pitches == (39,)
    assert by_w[61].pitches == (32,)
    assert by_w[62].pitches == (37,)
    assert by_w[63].pitches == (30,)
