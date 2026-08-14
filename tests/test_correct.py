from pathlib import Path

import numpy as np

from base_sheet.correct import correct_octave_errors, drop_short_notes, median_filter_pitches
from base_sheet.models import NoteEvent


def test_octave_jump_of_two_frames_is_repaired():
    # 40, then two frames at 52 (= +12), then 40
    midi = np.array([40, 52, 52, 40, 40], dtype=int)
    out = correct_octave_errors(midi, max_short_frames=2)
    assert list(out) == [40, 40, 40, 40, 40]


def test_real_octave_run_is_kept():
    midi = np.array([40, 52, 52, 52, 52], dtype=int)
    out = correct_octave_errors(midi, max_short_frames=2)
    assert list(out) == [40, 52, 52, 52, 52]


def test_median_filter_kills_one_frame_spike():
    midi = np.array([40, 40, 55, 40, 40], dtype=int)
    out = median_filter_pitches(midi, kernel_size=3)
    assert out[2] == 40


def test_drop_short_notes():
    notes = [
        NoteEvent(0.0, 0.02, 40),
        NoteEvent(0.1, 0.3, 41),
    ]
    kept = drop_short_notes(notes, min_duration=0.05)
    assert len(kept) == 1
    assert kept[0].pitch == 41
