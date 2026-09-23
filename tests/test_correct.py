import numpy as np

from base_sheet.correct import (
    choose_octave_from_spectrum,
    correct_note_octaves,
    correct_octave_errors,
    drop_short_notes,
    lift_missing_octave,
    median_filter_pitches,
    snap_register_to_neighbors,
    suppress_pitch_blips,
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


def test_pitch_blip_between_same_pitch_is_removed():
    notes = [
        NoteEvent(0.0, 1.0, 30),
        NoteEvent(1.0, 1.08, 43),
        NoteEvent(1.08, 2.0, 30),
    ]
    out = suppress_pitch_blips(notes)
    assert [n.pitch for n in out] == [30, 30]
    assert out[0].end == 1.08


def test_repeated_same_pitch_is_not_glued():
    notes = [
        NoteEvent(0.00, 0.23, 37),
        NoteEvent(0.24, 0.47, 37),
        NoteEvent(0.48, 0.71, 37),
    ]
    out = suppress_pitch_blips(notes)
    assert len(out) == 3
    assert [n.pitch for n in out] == [37, 37, 37]


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
    freqs = np.linspace(0, 500, 1001)
    mag = np.zeros_like(freqs)
    mag[(freqs >= 385) & (freqs <= 400)] = 1.0
    from base_sheet.correct import maybe_flageolet_pitch

    assert maybe_flageolet_pitch(mag, freqs, 36) == 67


def _tone(sr: int, seconds: float, *partials: tuple[float, float]) -> np.ndarray:
    t = np.arange(int(seconds * sr)) / sr
    y = np.zeros_like(t)
    for freq, amp in partials:
        y += amp * np.sin(2 * np.pi * freq * t)
    return y.astype(np.float32)


def test_lift_missing_octave_raises_e2_beside_a_high_neighbor():
    sr = 22050
    y = _tone(sr, 1.2, (82.41, 0.8))
    notes = [NoteEvent(0.05, 0.50, 45), NoteEvent(0.60, 1.10, 28)]
    out = lift_missing_octave(y, sr, notes)
    assert [n.pitch for n in out] == [45, 40]
    assert len(out) == 2


def test_lift_missing_octave_keeps_e1_when_fundamental_is_present():
    sr = 22050
    f = 41.20
    y = _tone(sr, 1.2, (f, 0.45), (2 * f, 0.9), (3 * f, 0.35))
    notes = [NoteEvent(0.05, 0.45, 45), NoteEvent(0.55, 1.10, 28)]
    out = lift_missing_octave(y, sr, notes)
    assert out[1].pitch == 28


def test_lift_missing_octave_does_not_raise_a_short_note_alone():
    sr = 22050
    y = _tone(sr, 0.8, (82.41, 0.8))
    notes = [NoteEvent(0.05, 0.50, 28)]
    out = lift_missing_octave(y, sr, notes)
    assert out[0].pitch == 28


def test_lift_missing_octave_raises_a_long_tone_with_no_low_fundamental():
    sr = 22050
    y = _tone(sr, 1.6, (92.50, 0.8))
    notes = [NoteEvent(0.05, 1.40, 30)]
    out = lift_missing_octave(y, sr, notes)
    assert out[0].pitch == 42


def test_spectrum_keeps_g2_when_odd_harmonics_belong_to_g2():
    freqs = np.linspace(0, 500, 1001)
    mag = np.zeros_like(freqs)
    mag[(freqs >= 94) & (freqs <= 102)] = 1.0  # G2
    mag[(freqs >= 190) & (freqs <= 202)] = 0.5
    mag[(freqs >= 286) & (freqs <= 302)] = 0.35
    assert choose_octave_from_spectrum(mag, freqs, 43) == 43
