from base_sheet.models import NoteEvent, QuantizedNote
from base_sheet.rhythm import merge_same_pitch, quantize, time_to_tick


def test_quantize_sixteenth_at_120_bpm():
    # 120 BPM → quarter = 0.5s, sixteenth = 0.125s
    notes = [NoteEvent(start=0.13, end=0.38, pitch=40, amplitude=0.8)]
    q = quantize(notes, bpm=120.0, grid="16")
    assert len(q) == 1
    assert q[0].offset_ql == 0.25  # one sixteenth
    assert q[0].pitch == 40


def test_time_to_tick_round():
    assert time_to_tick(0.0, 120, "16") == 0
    assert time_to_tick(0.125, 120, "16") == 1


def test_merge_adjacent_same_pitch():
    notes = [
        QuantizedNote(0.0, 0.5, 40, 80),
        QuantizedNote(0.5, 0.5, 40, 90),
        QuantizedNote(1.0, 0.5, 42, 80),
    ]
    merged = merge_same_pitch(notes)
    assert len(merged) == 2
    assert merged[0].duration_ql == 1.0
    assert merged[0].velocity == 90
    assert merged[1].pitch == 42
