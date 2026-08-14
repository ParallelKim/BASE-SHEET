import numpy as np

from base_sheet.models import NoteEvent
from base_sheet.segment import split_at_onsets


def test_same_pitch_splits_on_interior_onset():
    note = NoteEvent(start=0.0, end=1.0, pitch=40, amplitude=0.8)
    out = split_at_onsets([note], np.array([0.5]), min_duration=0.05)
    assert len(out) == 2
    assert out[0].end == 0.5
    assert out[1].start == 0.5
    assert out[0].pitch == out[1].pitch == 40


def test_onset_near_edge_does_not_split():
    note = NoteEvent(start=0.0, end=0.4, pitch=40)
    out = split_at_onsets([note], np.array([0.02]), min_duration=0.05)
    assert len(out) == 1
    assert out[0].start == 0.0 and out[0].end == 0.4
