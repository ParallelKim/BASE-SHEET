"""Turn an f0 contour into notes (CREPE Notes) and split repeated pitches.

CREPE Notes (Riley & Dixon, SMC 2023) combines inverted confidence with the
absolute f0 gradient, then confirms boundaries when median pitch differs by
≥1 semitone. Rock bass lines repeat the same pitch; those onsets are taken
from madmom when installed, otherwise librosa.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from base_sheet.models import MIN_NOTE_DURATION_S, NoteEvent, UNVOICED


def crepe_notes_boundary_signal(
    midi_pitches: np.ndarray,
    confidence: np.ndarray,
) -> np.ndarray:
    """Inverted confidence × normalized |Δpitch| (CREPE Notes)."""
    midi = midi_pitches.astype(float).copy()
    midi[midi < 0] = np.nan
    grad = np.abs(np.diff(midi, prepend=midi[0]))
    grad = np.nan_to_num(grad, nan=0.0)
    peak = float(np.max(grad)) if grad.size else 0.0
    if peak > 0:
        grad = grad / peak
    conf = np.clip(np.nan_to_num(confidence, nan=0.0), 0.0, 1.0)
    return (1.0 - conf) * grad


def crepe_notes_peaks(
    midi_pitches: np.ndarray,
    confidence: np.ndarray,
    threshold: float = 0.002,
) -> np.ndarray:
    combined = crepe_notes_boundary_signal(midi_pitches, confidence)
    peaks, _ = find_peaks(combined, height=threshold)
    return peaks


def _median_pitch(midi_pitches: np.ndarray, start: int, end: int) -> int | None:
    chunk = midi_pitches[start:end]
    voiced = chunk[chunk >= 0]
    if voiced.size == 0:
        return None
    return int(np.rint(np.median(voiced)))


def contour_to_notes(
    midi_pitches: np.ndarray,
    confidence: np.ndarray,
    times: np.ndarray,
    *,
    min_duration: float = MIN_NOTE_DURATION_S,
    boundary_threshold: float = 0.002,
    amplitudes: np.ndarray | None = None,
) -> list[NoteEvent]:
    """Segment a frame-wise MIDI contour into note events."""
    n = len(midi_pitches)
    if n == 0:
        return []

    split_at = {0, n}
    split_at.update(int(p) for p in crepe_notes_peaks(midi_pitches, confidence, boundary_threshold))
    for i in range(1, n):
        a, b = int(midi_pitches[i - 1]), int(midi_pitches[i])
        if (a < 0) != (b < 0):
            split_at.add(i)
        elif a >= 0 and b >= 0 and abs(a - b) >= 1:
            # keep CREPE Notes median-merge; still mark candidate splits
            split_at.add(i)

    cuts = sorted(split_at)
    raw: list[tuple[int, int, int, float]] = []
    for start, end in zip(cuts, cuts[1:]):
        if end <= start:
            continue
        pitch = _median_pitch(midi_pitches, start, end)
        if pitch is None:
            continue
        t0 = float(times[start])
        t1 = float(times[min(end, n) - 1])
        if end < n:
            t1 = float(times[end])
        elif n >= 2:
            t1 = float(times[-1] + (times[-1] - times[-2]))
        if t1 - t0 < min_duration:
            continue
        if amplitudes is not None:
            amp = float(np.mean(amplitudes[start:end]))
        else:
            amp = float(np.mean(confidence[start:end])) if confidence.size else 0.8
        raw.append((start, end, pitch, max(0.05, min(1.0, amp))))

    merged: list[tuple[int, int, int, float]] = []
    for item in raw:
        if merged and abs(item[2] - merged[-1][2]) < 1 and item[0] == merged[-1][1]:
            prev = merged[-1]
            merged[-1] = (prev[0], item[1], prev[2], max(prev[3], item[3]))
        else:
            merged.append(item)

    notes: list[NoteEvent] = []
    for start, end, pitch, amp in merged:
        t0 = float(times[start])
        t1 = float(times[end]) if end < n else float(times[-1] + 0.01)
        notes.append(NoteEvent(start=t0, end=t1, pitch=pitch, amplitude=amp))
    return notes


def detect_onsets(y: np.ndarray, sr: int | float) -> np.ndarray:
    """Onsets for repeated same-pitch notes. madmom if present, else librosa."""
    try:
        from madmom.features.onsets import CNNOnsetProcessor, peak_picking

        proc = CNNOnsetProcessor()
        act = proc(y)
        fps = 100
        peaks = peak_picking(act, threshold=0.5, smooth=None)
        return np.asarray(peaks, dtype=float) / float(fps)
    except Exception:
        import librosa

        return librosa.onset.onset_detect(y=y, sr=sr, units="time", backtrack=True)


def split_at_onsets(
    notes: list[NoteEvent],
    onsets: np.ndarray,
    min_duration: float = MIN_NOTE_DURATION_S,
) -> list[NoteEvent]:
    """Split a sustained pitch where an onset falls inside the note.

    CREPE Notes: same-pitch repeats have ~0 pitch gradient, so an onset
    detector is required (especially for rock bass).
    """
    if not notes:
        return []
    onset_list = [float(o) for o in np.atleast_1d(onsets)]
    out: list[NoteEvent] = []
    for note in notes:
        cuts = [note.start]
        for onset in onset_list:
            if note.start + min_duration <= onset <= note.end - min_duration:
                cuts.append(onset)
        cuts.append(note.end)
        cuts = sorted(cuts)
        for start, end in zip(cuts, cuts[1:]):
            if end - start >= min_duration:
                out.append(
                    NoteEvent(
                        start=start,
                        end=end,
                        pitch=note.pitch,
                        amplitude=note.amplitude,
                    )
                )
    return out


def split_repeats_on_meter(
    y: np.ndarray,
    sr: int | float,
    notes: list[NoteEvent],
    bpm: float,
    grid: str = "8",
    *,
    peak_ratio: float = 0.35,
) -> list[NoteEvent]:
    """Split a held pitch where the envelope re-attacks on the metrical grid.

    Same-pitch eighths have ~0 f0 gradient, so contour segmentation cannot
    see them. A decaying whole note has one attack; repeated 8ths re-peak
    near each grid tick at a large fraction of that attack.
    """
    import librosa

    from base_sheet.rhythm import seconds_per_tick

    if not notes:
        return []
    hop = 256
    rms = librosa.feature.rms(y=y, hop_length=hop, frame_length=hop * 4)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    tick = seconds_per_tick(bpm, grid)
    min_dur = max(0.05, 0.55 * tick)
    half = 0.5 * tick
    win = min(0.08, 0.35 * tick)

    def env_near(t: float) -> float:
        if len(rms) == 0:
            return 0.0
        mask = (times >= t - win) & (times <= t + win)
        if not np.any(mask):
            idx = int(np.clip(np.searchsorted(times, t), 0, len(rms) - 1))
            return float(rms[idx])
        return float(np.max(rms[mask]))

    out: list[NoteEvent] = []
    for note in notes:
        attack = max(env_near(note.start), env_near(note.start + 0.02), 1e-6)
        cuts = [note.start]
        t = note.start + tick
        while t <= note.end - min_dur + 1e-9:
            peak = env_near(t)
            trough = env_near(t - half)
            reattack = peak >= 1.2 * max(trough, 1e-6) and peak >= 0.2 * attack
            if reattack:
                cuts.append(float(t))
            t += tick
        cuts.append(note.end)
        dedup: list[float] = []
        for cut in cuts:
            if not dedup or cut - dedup[-1] >= min_dur * 0.5:
                dedup.append(cut)
            else:
                dedup[-1] = cut
        if dedup[-1] != note.end:
            dedup.append(note.end)
        for start, end in zip(dedup, dedup[1:]):
            if end - start >= min_dur:
                out.append(
                    NoteEvent(
                        start=start,
                        end=end,
                        pitch=note.pitch,
                        amplitude=note.amplitude,
                    )
                )
            elif out and out[-1].pitch == note.pitch:
                prev = out[-1]
                out[-1] = NoteEvent(
                    start=prev.start,
                    end=end,
                    pitch=prev.pitch,
                    amplitude=prev.amplitude,
                )
    return out
