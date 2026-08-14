"""Bass-range folding, median smoothing, and octave-jump repair.

Recipes follow BassLift (MIT): rolling median on MIDI frames and collapsing
±12 jumps that last only a few frames. Adapted to keep unvoiced frames as -1.
Note-level octave choice uses a short harmonic-series score so CREPE/pYIN
tracking the first harmonic can drop back to the sounding bass pitch.
"""

from __future__ import annotations

import numpy as np

from base_sheet.models import (
    BASS_MIDI_MAX,
    BASS_MIDI_MIN,
    MIN_NOTE_DURATION_S,
    UNVOICED,
    NoteEvent,
)

# Typical rock/pop 4-string register (E1–C3). Above this, +12 is often H1.
_TYPICAL_BASS_HIGH = 48


def fold_to_bass_range(
    midi_pitch: int,
    low: int = BASS_MIDI_MIN,
    high: int = BASS_MIDI_MAX,
) -> int | None:
    """Shift by octaves into the bass range, or return None if impossible."""
    pitch = int(midi_pitch)
    while pitch > high:
        pitch -= 12
    while pitch < low:
        pitch += 12
    if pitch < low or pitch > high:
        return None
    return pitch


def fold_frame_pitches(midi_pitches: np.ndarray) -> np.ndarray:
    out = midi_pitches.copy()
    for i, value in enumerate(out):
        if int(value) < 0:
            continue
        folded = fold_to_bass_range(int(value))
        out[i] = folded if folded is not None else UNVOICED
    return out


def median_filter_pitches(midi_pitches: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Smooth 1–2 frame pitch outliers using a rolling median (BassLift)."""
    n = len(midi_pitches)
    if n < 3:
        return midi_pitches.copy()
    ks = min(kernel_size, n if n % 2 == 1 else n - 1)
    if ks < 3:
        return midi_pitches.copy()
    pad = ks // 2
    padded = np.pad(midi_pitches.astype(float), pad, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, ks)
    med = np.median(windows, axis=1)
    voiced = midi_pitches >= 0
    out = midi_pitches.copy()
    out[voiced] = np.rint(med[voiced]).astype(int)
    return out


def correct_octave_errors(midi_pitches: np.ndarray, max_short_frames: int = 5) -> np.ndarray:
    """Fix octave jumps (±12) that last only a few frames (BassLift / pYIN)."""
    result = midi_pitches.copy()
    n = len(result)
    if n < 3:
        return result
    i = 0
    while i < n:
        base = int(result[i])
        j = i + 1
        while j < n and abs(int(result[j]) - base) == 12:
            j += 1
        run_len = j - i - 1
        if 0 < run_len <= max_short_frames and base >= 0:
            for k in range(i + 1, j):
                if BASS_MIDI_MIN <= base <= BASS_MIDI_MAX:
                    result[k] = base
        i = j if run_len > 0 else i + 1
    return result


def apply_confidence_mask(
    midi_pitches: np.ndarray,
    confidence: np.ndarray,
    floor: float,
) -> np.ndarray:
    out = midi_pitches.copy()
    out[np.asarray(confidence) < floor] = UNVOICED
    return out


def drop_short_notes(
    notes: list[NoteEvent],
    min_duration: float = MIN_NOTE_DURATION_S,
) -> list[NoteEvent]:
    return [n for n in notes if n.duration >= min_duration]


def correct_contour(
    midi_pitches: np.ndarray,
    confidence: np.ndarray | None = None,
    *,
    confidence_floor: float = 0.21,
) -> np.ndarray:
    midi = midi_pitches.astype(int).copy()
    if confidence is not None:
        midi = apply_confidence_mask(midi, confidence, confidence_floor)
    midi = median_filter_pitches(midi)
    midi = correct_octave_errors(midi)
    midi = fold_frame_pitches(midi)
    return midi


def _band_energy(mag: np.ndarray, freqs: np.ndarray, hz: float, rel_bw: float = 0.08) -> float:
    if hz <= 0 or mag.size == 0:
        return 0.0
    lo, hi = hz * (1.0 - rel_bw), hz * (1.0 + rel_bw)
    mask = (freqs >= lo) & (freqs <= hi)
    if not np.any(mask):
        return 0.0
    return float(np.mean(mag[mask]))


def _harmonic_score(mag: np.ndarray, freqs: np.ndarray, midi_pitch: int) -> float:
    import librosa

    f0 = float(librosa.midi_to_hz(int(midi_pitch)))
    e1 = _band_energy(mag, freqs, f0)
    e2 = _band_energy(mag, freqs, 2.0 * f0)
    e3 = _band_energy(mag, freqs, 3.0 * f0)
    score = e1 + 0.55 * e2 + 0.35 * e3
    if midi_pitch <= _TYPICAL_BASS_HIGH:
        score *= 1.12
    return score


def choose_octave_from_spectrum(
    mag: np.ndarray,
    freqs: np.ndarray,
    midi_pitch: int,
) -> int:
    """Pick f0 vs ±12 using harmonic-series energy in a magnitude spectrum."""
    folded = fold_to_bass_range(int(midi_pitch))
    if folded is None:
        return int(midi_pitch)
    candidates = [folded]
    if folded - 12 >= BASS_MIDI_MIN:
        candidates.append(folded - 12)
    if folded + 12 <= BASS_MIDI_MAX:
        candidates.append(folded + 12)
    scored = [(_harmonic_score(mag, freqs, p), -abs(p - 36), p) for p in candidates]
    return max(scored)[2]


def correct_note_octaves(
    y: np.ndarray,
    sr: int | float,
    notes: list[NoteEvent],
) -> list[NoteEvent]:
    """Re-choose each note's octave from the stem spectrum (f vs 2f)."""
    import librosa

    if not notes:
        return []
    hop = 512
    n_fft = 4096
    stft = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=float(sr), n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(stft.shape[1]), sr=sr, hop_length=hop)
    out: list[NoteEvent] = []
    for note in notes:
        body0 = note.start + min(0.03, 0.25 * note.duration)
        body1 = note.end
        mask = (times >= body0) & (times < body1)
        if not np.any(mask):
            idx = int(np.clip(np.searchsorted(times, note.start), 0, stft.shape[1] - 1))
            mag = stft[:, idx]
        else:
            mag = np.median(stft[:, mask], axis=1)
        pitch = choose_octave_from_spectrum(mag, freqs, note.pitch)
        out.append(
            NoteEvent(start=note.start, end=note.end, pitch=pitch, amplitude=note.amplitude)
        )
    return snap_register_to_neighbors(out)


def snap_register_to_neighbors(notes: list[NoteEvent], window_s: float = 2.0) -> list[NoteEvent]:
    """Fold isolated highs that sit an octave above nearby bass notes."""
    if not notes:
        return []
    ordered = sorted(notes, key=lambda n: n.start)
    pitches = np.array([n.pitch for n in ordered], dtype=int)
    starts = np.array([n.start for n in ordered], dtype=float)
    out: list[NoteEvent] = []
    for i, note in enumerate(ordered):
        local = pitches[np.abs(starts - note.start) <= window_s]
        if local.size == 0:
            out.append(note)
            continue
        med = float(np.median(local))
        pitch = int(note.pitch)
        lowered = pitch - 12
        if (
            pitch >= 43
            and lowered >= BASS_MIDI_MIN
            and abs(lowered - med) + 3 < abs(pitch - med)
        ):
            pitch = lowered
        out.append(
            NoteEvent(start=note.start, end=note.end, pitch=pitch, amplitude=note.amplitude)
        )
    return out
