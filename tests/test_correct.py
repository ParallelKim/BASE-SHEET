import numpy as np

from base_sheet.correct import (
    choose_octave_from_spectrum,
    correct_note_octaves,
    correct_octave_errors,
    drop_short_notes,
    median_filter_pitches,
    snap_register_to_neighbors,
)
from base_sheet.models import NoteEvent


def test_octave_jump_of_two_frames_is_repaired():
    # 40, then two frames at 52 (= +12), then 40
    midi = np.array([40, 52, 52, 40, 40], dtype=int)
    out = correct_octave_errors(midi, max_short_frames=5)
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


def test_spectrum_prefers_bass_fundamental_over_h1():
    freqs = np.linspace(0, 400, 801)
    mag = np.zeros_like(freqs)
    mag[(freqs >= 58) & (freqs <= 66)] = 0.4  # B1
    mag[(freqs >= 118) & (freqs <= 130)] = 1.0  # H1 (what CREPE often tracks)
    mag[(freqs >= 178) & (freqs <= 192)] = 0.5
    assert choose_octave_from_spectrum(mag, freqs, 47) == 35


def test_correct_note_octaves_drops_h1_on_b1_tone():
    sr = 22050
    t = np.arange(int(0.8 * sr)) / sr
    f = 61.74
    y = (0.35 * np.sin(2 * np.pi * f * t) + 0.9 * np.sin(2 * np.pi * 2 * f * t)).astype(
        np.float32
    )
    notes = [NoteEvent(0.05, 0.7, 47, 0.8)]
    out = correct_note_octaves(y, sr, notes)
    assert out[0].pitch == 35


def test_snap_register_folds_isolated_high():
    notes = [
        NoteEvent(0.0, 0.2, 35),
        NoteEvent(0.2, 0.4, 47),
        NoteEvent(0.4, 0.6, 30),
    ]
    out = snap_register_to_neighbors(notes)
    assert out[1].pitch == 35


def test_spectrum_prefers_e1_over_h1_e2():
    freqs = np.linspace(0, 400, 801)
    mag = np.zeros_like(freqs)
    mag[(freqs >= 38) & (freqs <= 46)] = 0.25  # E1, weaker than H1
    mag[(freqs >= 78) & (freqs <= 88)] = 1.0
    mag[(freqs >= 118) & (freqs <= 130)] = 0.45
    assert choose_octave_from_spectrum(mag, freqs, 40) == 28


def test_spectrum_prefers_fsharp1_over_h1():
    freqs = np.linspace(0, 400, 801)
    mag = np.zeros_like(freqs)
    mag[(freqs >= 42) & (freqs <= 52)] = 0.22
    mag[(freqs >= 86) & (freqs <= 100)] = 1.0
    mag[(freqs >= 132) & (freqs <= 148)] = 0.4
    assert choose_octave_from_spectrum(mag, freqs, 42) == 30


def test_pure_e2_sine_keeps_e2():
    sr = 22050
    t = np.arange(int(0.8 * sr)) / sr
    y = (0.7 * np.sin(2 * np.pi * 82.41 * t)).astype(np.float32)
    notes = [NoteEvent(0.05, 0.7, 40, 0.8)]
    out = correct_note_octaves(y, sr, notes)
    assert out[0].pitch == 40


def test_snap_register_folds_e2_next_to_e1():
    notes = [
        NoteEvent(0.0, 0.2, 28),
        NoteEvent(0.2, 0.4, 30),
        NoteEvent(0.4, 0.6, 40),
        NoteEvent(0.6, 0.8, 28),
        NoteEvent(0.8, 1.0, 42),
        NoteEvent(1.0, 1.2, 30),
    ]
    out = snap_register_to_neighbors(notes)
    assert out[2].pitch == 28
    assert out[4].pitch == 30


def test_snap_register_keeps_mixed_g2_among_open_strings():
    notes = [
        NoteEvent(0.0, 0.2, 28),
        NoteEvent(0.2, 0.4, 33),
        NoteEvent(0.4, 0.6, 43),
        NoteEvent(0.6, 0.8, 38),
        NoteEvent(0.8, 1.0, 28),
        NoteEvent(1.0, 1.2, 33),
    ]
    out = snap_register_to_neighbors(notes)
    assert out[2].pitch == 43


def test_snap_register_keeps_octave_jumps_when_both_are_common():
    notes = [
        NoteEvent(0.0, 0.2, 36),
        NoteEvent(0.2, 0.4, 36),
        NoteEvent(0.4, 0.6, 48),
        NoteEvent(0.6, 0.8, 48),
        NoteEvent(0.8, 1.0, 46),
        NoteEvent(1.0, 1.2, 43),
        NoteEvent(1.2, 1.4, 36),
        NoteEvent(1.4, 1.6, 48),
    ]
    out = snap_register_to_neighbors(notes)
    assert [n.pitch for n in out] == [36, 36, 48, 48, 46, 43, 36, 48]


def test_snap_register_keeps_c3_when_c2_is_only_slightly_more_common():
    notes = [
        NoteEvent(0.0, 0.2, 36),
        NoteEvent(0.2, 0.4, 36),
        NoteEvent(0.4, 0.6, 36),
        NoteEvent(0.6, 0.8, 36),
        NoteEvent(0.8, 1.0, 48),
        NoteEvent(1.0, 1.2, 48),
        NoteEvent(1.2, 1.4, 46),
        NoteEvent(1.4, 1.6, 43),
    ]
    out = snap_register_to_neighbors(notes)
    assert out[4].pitch == 48
    assert out[5].pitch == 48


def test_snap_register_keeps_flageolet_g4():
    notes = [
        NoteEvent(0.0, 0.2, 36),
        NoteEvent(0.2, 0.6, 67),
        NoteEvent(0.6, 0.8, 36),
    ]
    out = snap_register_to_neighbors(notes)
    assert out[1].pitch == 67


def test_flageolet_g4_sine_is_not_folded_to_open_string():
    sr = 22050
    t = np.arange(int(0.7 * sr)) / sr
    y = (0.65 * np.sin(2 * np.pi * 392.0 * t)).astype(np.float32)
    notes = [NoteEvent(0.05, 0.55, 36, 0.8)]
    out = correct_note_octaves(y, sr, notes)
    assert out[0].pitch == 67


def test_spectrum_keeps_g2_when_odd_harmonics_belong_to_g2():
    freqs = np.linspace(0, 500, 1001)
    mag = np.zeros_like(freqs)
    mag[(freqs >= 94) & (freqs <= 102)] = 1.0  # G2
    mag[(freqs >= 190) & (freqs <= 202)] = 0.5
    mag[(freqs >= 286) & (freqs <= 302)] = 0.35
    assert choose_octave_from_spectrum(mag, freqs, 43) == 43
