import numpy as np

from base_sheet.models import NoteEvent
from base_sheet.segment import (
    detect_bass_onsets,
    split_at_onsets,
    split_repeated_pitches,
    split_repeats_on_meter,
)


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


def _pluck_train(n: int, eighth: float, sr: int, freq: float) -> np.ndarray:
    y = np.zeros(int((n * eighth + 0.1) * sr), dtype=np.float32)
    pluck = int(0.06 * sr)
    t = np.arange(pluck) / sr
    burst = 0.6 * np.sin(2 * np.pi * freq * t) * np.hanning(pluck)
    for i in range(n):
        a = int(i * eighth * sr)
        y[a : a + pluck] += burst
    return y


def test_meter_split_cuts_repeated_eighth_plucks():
    sr = 22050
    bpm = 120.0
    eighth = 0.25
    y = _pluck_train(16, eighth, sr, freq=61.74)
    held = [NoteEvent(start=0.0, end=4.0, pitch=35, amplitude=0.8)]
    out = split_repeats_on_meter(y, sr, held, bpm, grid="8")
    assert 8 <= len(out) <= 18


def test_meter_split_keeps_single_decay():
    sr = 22050
    n = int(2.0 * sr)
    t = np.arange(n) / sr
    y = (0.5 * np.sin(2 * np.pi * 61.74 * t) * np.exp(-t * 2.0)).astype(np.float32)
    held = [NoteEvent(start=0.0, end=2.0, pitch=35, amplitude=0.8)]
    out = split_repeats_on_meter(y, sr, held, bpm=120.0, grid="8")
    assert len(out) <= 3


def test_pluck_train_onsets_near_eighths():
    sr = 22050
    bpm = 120.0
    eighth = 0.25
    y = _pluck_train(16, eighth, sr, freq=61.74)
    onsets = detect_bass_onsets(y, sr, bpm=bpm)
    assert 10 <= len(onsets) <= 22


def test_split_repeated_pitches_uses_onsets_then_meter():
    sr = 22050
    bpm = 120.0
    eighth = 0.25
    y = _pluck_train(16, eighth, sr, freq=61.74)
    held = [NoteEvent(start=0.0, end=4.0, pitch=35, amplitude=0.8)]
    out = split_repeated_pitches(y, sr, held, bpm, grid="8")
    assert 12 <= len(out) <= 20
