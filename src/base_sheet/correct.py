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


def _band_energy(mag: np.ndarray, freqs: np.ndarray, hz: float, rel_bw: float | None = None) -> float:
    if hz <= 0 or mag.size == 0:
        return 0.0
    # E1–F#1 sit in few STFT bins; a wider band is required to see the fundamental.
    if rel_bw is None:
        rel_bw = 0.16 if hz < 80.0 else 0.08
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
    # Log so a weak bass fundamental can still beat a loud H1.
    score = float(np.log(e1 + 1e-8) + 0.65 * np.log(e2 + 1e-8) + 0.35 * np.log(e3 + 1e-8))
    if 28 <= midi_pitch <= 38:
        score += 0.55
    elif midi_pitch >= 40:
        score -= 0.25
    return score


def choose_octave_from_spectrum(
    mag: np.ndarray,
    freqs: np.ndarray,
    midi_pitch: int,
) -> int:
    """Pick f0 vs ±12.

    CREPE often reports H1. A real lower bass note still has odd harmonics
    (3f, 5f) and sometimes a weak fundamental; a pure higher note does not.
    """
    import librosa

    folded = fold_to_bass_range(int(midi_pitch))
    if folded is None:
        return int(midi_pitch)
    lower = folded - 12
    if lower < BASS_MIDI_MIN:
        return folded
    f_hi = float(librosa.midi_to_hz(folded))
    f_lo = float(librosa.midi_to_hz(lower))
    e_lo = _band_energy(mag, freqs, f_lo)
    e_hi = _band_energy(mag, freqs, f_hi)
    e3_lo = _band_energy(mag, freqs, 3.0 * f_lo)
    e3_hi = _band_energy(mag, freqs, 3.0 * f_hi)
    e5_lo = _band_energy(mag, freqs, 5.0 * f_lo)
    peak = max(e_hi, 1e-9)
    has_f0 = e_lo >= 0.07 * peak
    has_odd = (e3_lo + 0.5 * e5_lo) >= 0.12 * peak
    # Odd harmonics of the *lower* pitch must beat those of the higher one.
    # Otherwise a real G2/A2 (or a harmonic) is folded because 3f of E1
    # leaks into the same band as the higher note's body.
    lower_is_f0 = has_f0 or has_odd
    if folded >= 55 and e_hi >= 1.5 * max(e_lo, 1e-12):
        return folded
    if folded >= 40 and lower_is_f0 and e3_lo > 1.15 * max(e3_hi, 1e-12):
        return lower
    if folded >= 40:
        return folded
    scored = [
        (_harmonic_score(mag, freqs, p), -abs(p - 33), p)
        for p in (folded, lower)
        if p >= BASS_MIDI_MIN
    ]
    return max(scored)[2]


def midi_from_spectrum_peak(
    mag: np.ndarray,
    freqs: np.ndarray,
    *,
    lo_hz: float = 80.0,
    hi_hz: float = 430.0,
) -> int | None:
    """MIDI of the strongest spectral peak in the bass/flageolet band."""
    import librosa

    mask = (freqs >= lo_hz) & (freqs <= hi_hz)
    if not np.any(mask):
        return None
    idx = int(np.argmax(mag[mask]))
    hz = float(np.asarray(freqs[mask])[idx])
    if hz <= 0:
        return None
    midi = int(round(float(librosa.hz_to_midi(hz))))
    return fold_to_bass_range(midi)


def maybe_flageolet_pitch(mag: np.ndarray, freqs: np.ndarray, midi_pitch: int) -> int:
    """If the sounding tone is a high natural harmonic, keep that pitch.

    CREPE often unvoices flageolet notes or reports a low string residual.
    Slap transients are broadband — only lift a *tonal* peak at MIDI ≥ 55
    with almost no energy an octave below.
    """
    import librosa

    peak_midi = midi_from_spectrum_peak(mag, freqs)
    if peak_midi is None or peak_midi < 55:
        return int(midi_pitch)
    f_pk = float(librosa.midi_to_hz(peak_midi))
    e_pk = _band_energy(mag, freqs, f_pk, rel_bw=0.04)
    e_half = _band_energy(mag, freqs, 0.5 * f_pk)
    e_third = _band_energy(mag, freqs, f_pk / 3.0)
    band = (freqs >= 80.0) & (freqs <= 430.0)
    narrow = (freqs >= f_pk * 0.97) & (freqs <= f_pk * 1.03)
    total = float(np.sum(mag[band])) + 1e-9
    tonality = float(np.sum(mag[narrow])) / total
    if (
        e_pk >= 1e-8
        and tonality >= 0.22
        and e_half < 0.22 * e_pk
        and e_third < 0.28 * e_pk
    ):
        return peak_midi
    return int(midi_pitch)


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
    n_fft = 8192
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
        lifted = maybe_flageolet_pitch(mag, freqs, pitch)
        if lifted >= 55 and lifted != pitch:
            import librosa

            e_cur = _band_energy(mag, freqs, float(librosa.midi_to_hz(pitch)))
            e_new = _band_energy(mag, freqs, float(librosa.midi_to_hz(lifted)))
            if e_new >= 3.5 * max(e_cur, 1e-9):
                pitch = lifted
        out.append(
            NoteEvent(start=note.start, end=note.end, pitch=pitch, amplitude=note.amplitude)
        )
    return snap_register_to_neighbors(out)


def snap_register_to_neighbors(notes: list[NoteEvent], window_s: float = 2.0) -> list[NoteEvent]:
    """Fold a likely H1 when the same pitch class is mostly an octave down.

    Do not fold just because a neighbor exists at -12: bass lines jump
    octaves (C2 then C3) on purpose. Only fold when the lower pitch
    dominates the local window, or the high is a single isolated spike.
    """
    if not notes:
        return []
    ordered = sorted(notes, key=lambda n: n.start)
    pitches = [int(n.pitch) for n in ordered]
    starts = np.array([n.start for n in ordered], dtype=float)
    out: list[NoteEvent] = []
    for i, note in enumerate(ordered):
        local = [
            pitches[j]
            for j in range(len(ordered))
            if abs(float(starts[j]) - float(starts[i])) <= window_s
        ]
        n_at: dict[int, int] = {}
        for p in local:
            n_at[p] = n_at.get(p, 0) + 1
        pitch = pitches[i]
        while pitch - 12 >= BASS_MIDI_MIN:
            low = pitch - 12
            n_hi = n_at.get(pitch, 0)
            n_lo = n_at.get(low, 0)
            isolated = n_hi == 1 and n_lo >= 1
            # 2× is too weak for C2/C3 riffs (often 4 low vs 2 high in 2 s).
            dominated = n_lo >= 3 * n_hi and n_lo >= 6
            if not (isolated or dominated):
                break
            pitch = low
        out.append(
            NoteEvent(start=note.start, end=note.end, pitch=pitch, amplitude=note.amplitude)
        )
    return out
