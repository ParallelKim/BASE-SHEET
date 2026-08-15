from sheet_score import Hit, bar8, choose_t0, expand_play_order, score_hits, sustain
from base_sheet.models import NoteEvent


def test_bar8_has_eight_hits():
    hits = bar8(35, 2)
    assert len(hits) == 8
    assert hits[0].bar == 2 and hits[0].pitch == 35
    assert hits[-1].eighth == 7.0


def test_expand_play_order_reindexes_bars():
    written = [bar8(28, 0), bar8(30, 1)]
    out = expand_play_order(written, [1, 0, 1])
    assert [h.bar for h in out[0:8]] == [0] * 8
    assert out[0].pitch == 30
    assert out[8].pitch == 28
    assert out[16].pitch == 30


def test_score_hits_exact_on_synthetic_notes():
    hits = bar8(35, 0) + bar8(30, 1)
    notes = [
        NoteEvent(i * 0.25, (i + 1) * 0.25, 35 if i < 8 else 30) for i in range(16)
    ]
    # 120 bpm → eighth = 0.25 s, t0 = 0
    sc = score_hits(notes, hits, bpm=120.0, t0=0.0)
    assert sc.pitch_exact == 1.0
    assert sc.pitch_chroma == 1.0
    assert sc.missing == 0


def test_choose_t0_recovers_one_eighth_shift():
    hits = [sustain(40, 0, 0.0, 8.0)]
    notes = [NoteEvent(0.25, 2.0, 40)]
    t0 = choose_t0(notes, hits, bpm=120.0)
    sc = score_hits(notes, hits, bpm=120.0, t0=t0)
    assert sc.sounding == 1
    assert sc.pitch_exact == 1.0
