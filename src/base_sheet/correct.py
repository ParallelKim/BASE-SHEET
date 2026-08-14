"""Bass-range folding, median smoothing, and short octave-jump repair.

Recipes follow BassLift (MIT): rolling median on MIDI frames and collapsing
±12 jumps that last only 1–2 frames. Adapted to keep unvoiced frames as -1.
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


def correct_octave_errors(midi_pitches: np.ndarray, max_short_frames: int = 2) -> np.ndarray:
    """Fix octave jumps (±12) that last only 1–2 frames (BassLift / pYIN)."""
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
