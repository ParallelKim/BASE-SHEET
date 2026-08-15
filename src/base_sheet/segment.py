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


def _nms_times(times: np.ndarray, min_gap: float) -> np.ndarray:
    if times.size == 0:
        return times.astype(float)
    ordered = np.sort(np.asarray(times, dtype=float))
    kept = [float(ordered[0])]
    for t in ordered[1:]:
        if t - kept[-1] >= min_gap:
            kept.append(float(t))
    return np.asarray(kept, dtype=float)


def detect_bass_onsets(
    y: np.ndarray,
    sr: int | float,
    bpm: float | None = None,
) -> np.ndarray:
    """Pluck onsets from low-mid spectral flux, plus madmom if installed.

    Rock bass repeats the same pitch; f0 gradient is ~0, so this detector
    is what actually finds the 8th-note attacks.
    """
    import librosa

    hop = 256
    n_fft = 2048
    spec = np.abs(librosa.stft(np.asarray(y, dtype=float), n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=float(sr), n_fft=n_fft)
    band = (freqs >= 50.0) & (freqs <= 1800.0)
    env = librosa.onset.onset_strength(S=spec[band, :], sr=float(sr), hop_length=hop)
    wait = 1
    if bpm is not None and bpm > 0:
        # Allow 16ths; suppress double-triggers closer than ~40 ms.
        wait = max(1, int((60.0 / float(bpm) / 8.0) * float(sr) / hop * 0.45))
    times = librosa.onset.onset_detect(
        onset_envelope=env,
        sr=float(sr),
        hop_length=hop,
        units="time",
        backtrack=True,
        delta=0.07,
        wait=wait,
    )
    extra: list[float] = []
    try:
        from madmom.features.onsets import CNNOnsetProcessor, peak_picking

        proc = CNNOnsetProcessor()
        act = proc(y)
        extra = [float(p) / 100.0 for p in peak_picking(act, threshold=0.45, smooth=None)]
    except Exception:
        extra = []
    merged = np.concatenate([np.atleast_1d(times).astype(float), np.asarray(extra, dtype=float)])
    return _nms_times(merged, 0.04)


def detect_onsets(y: np.ndarray, sr: int | float) -> np.ndarray:
    """Onsets for repeated same-pitch notes."""
    return detect_bass_onsets(y, sr)


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
    near each grid tick. Cut times snap to the local onset-envelope peak so
    the MIDI attack matches the stem, not the metronome.
    """
    import librosa

    from base_sheet.rhythm import seconds_per_tick

    del peak_ratio
    if not notes:
        return []
    hop = 256
    rms = librosa.feature.rms(y=y, hop_length=hop, frame_length=512)[0]
    spec = np.abs(librosa.stft(np.asarray(y, dtype=float), n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=float(sr), n_fft=2048)
    band = (freqs >= 50.0) & (freqs <= 1800.0)
    onset_env = librosa.onset.onset_strength(S=spec[band, :], sr=float(sr), hop_length=hop)
    n_frames = min(len(rms), len(onset_env), spec.shape[1])
    rms = rms[:n_frames]
    onset_env = onset_env[:n_frames]
    times = librosa.frames_to_time(np.arange(n_frames), sr=sr, hop_length=hop)
    tick = seconds_per_tick(bpm, grid)
    min_dur = max(0.05, 0.55 * tick)
    half = 0.5 * tick
    win = min(0.07, 0.28 * tick)

    def _max_near(arr: np.ndarray, t: float) -> tuple[float, float]:
        if arr.size == 0:
            return 0.0, t
        mask = (times >= t - win) & (times <= t + win)
        if not np.any(mask):
            idx = int(np.clip(np.searchsorted(times, t), 0, len(arr) - 1))
            return float(arr[idx]), float(times[idx])
        local = arr[mask]
        local_t = times[mask]
        k = int(np.argmax(local))
        return float(local[k]), float(local_t[k])

    def _at(arr: np.ndarray, t: float) -> float:
        if arr.size == 0:
            return 0.0
        idx = int(np.clip(np.searchsorted(times, t), 0, len(arr) - 1))
        return float(arr[idx])

    def rms_near(t: float) -> float:
        return _max_near(rms, t)[0]

    out: list[NoteEvent] = []
    for note in notes:
        attack = max(rms_near(note.start), rms_near(note.start + 0.02), 1e-6)
        note_mask = (times >= note.start) & (times < note.end)
        env_floor = float(np.percentile(onset_env[note_mask], 55)) if np.any(note_mask) else 0.0
        cuts = [note.start]
        t = note.start + tick
        while t <= note.end - min_dur + 1e-9:
            peak, peak_t = _max_near(rms, t)
            flux, flux_t = _max_near(onset_env, t)
            trough = _at(rms, t - half)
            reattack = peak >= 1.25 * max(trough, 1e-6) and peak >= 0.13 * attack
            if reattack:
                cut = flux_t if flux >= env_floor else peak_t
                if note.start + min_dur <= cut <= note.end - min_dur:
                    cuts.append(float(cut))
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
        parent: list[NoteEvent] = []
        for start, end in zip(dedup, dedup[1:]):
            if end - start >= min_dur:
                parent.append(
                    NoteEvent(
                        start=start,
                        end=end,
                        pitch=note.pitch,
                        amplitude=note.amplitude,
                    )
                )
            elif parent:
                prev = parent[-1]
                parent[-1] = NoteEvent(
                    start=prev.start,
                    end=end,
                    pitch=prev.pitch,
                    amplitude=prev.amplitude,
                )
            elif end - start >= MIN_NOTE_DURATION_S:
                parent.append(
                    NoteEvent(
                        start=start,
                        end=end,
                        pitch=note.pitch,
                        amplitude=note.amplitude,
                    )
                )
        out.extend(parent)
    return out


def _seed_holes_at_onsets(
    notes: list[NoteEvent],
    onsets: np.ndarray,
    tick: float,
    y: np.ndarray | None = None,
    sr: int | float | None = None,
) -> list[NoteEvent]:
    """If f0 dropped out between plucks, still put a note on the attack."""
    if not notes:
        return []
    ordered = sorted(notes, key=lambda n: n.start)
    extra: list[NoteEvent] = []
    min_hole = 0.45 * tick
    mag_at = None
    freqs = None
    times = None
    stft = None
    if y is not None and sr is not None:
        import librosa

        hop = 512
        stft = np.abs(librosa.stft(np.asarray(y, dtype=float), n_fft=4096, hop_length=hop))
        freqs = librosa.fft_frequencies(sr=float(sr), n_fft=4096)
        times = librosa.frames_to_time(np.arange(stft.shape[1]), sr=sr, hop_length=hop)

        def mag_at(t: float) -> np.ndarray:
            idx = int(np.clip(np.searchsorted(times, t), 0, stft.shape[1] - 1))
            return stft[:, idx]

    for onset in np.atleast_1d(onsets).astype(float):
        covered = any(n.start - 0.02 <= onset < n.end for n in ordered)
        if covered:
            continue
        prev = [n for n in ordered if n.end <= onset + 1e-6]
        nxt = [n for n in ordered if n.start >= onset - 1e-6]
        gap_start = prev[-1].end if prev else onset - tick
        gap_end = nxt[0].start if nxt else onset + tick
        if gap_end - gap_start < min_hole:
            continue
        nearest = min(
            ordered,
            key=lambda n: min(abs(n.start - onset), abs(n.end - onset)),
        )
        pitch = nearest.pitch
        if mag_at is not None and freqs is not None:
            from base_sheet.correct import maybe_flageolet_pitch, midi_from_spectrum_peak

            mag = mag_at(onset)
            peaked = midi_from_spectrum_peak(mag, freqs)
            if peaked is not None:
                pitch = maybe_flageolet_pitch(mag, freqs, peaked)
        extra.append(
            NoteEvent(
                start=float(onset),
                end=min(float(onset) + 0.85 * tick, gap_end),
                pitch=pitch,
                amplitude=nearest.amplitude,
            )
        )
    return sorted(ordered + extra, key=lambda n: n.start)


def _confirmed_reattacks(
    y: np.ndarray,
    sr: int | float,
    onsets: np.ndarray,
    tick: float,
) -> np.ndarray:
    """Keep onsets with a real low-band flux jump; drop RMS vibrato shimmer.

    Slap/pop attacks often do not dip in RMS between hits, so RMS ratio
    misses them. Fingerstyle sustain wobbles RMS without flux.
    """
    import librosa

    if onsets.size == 0:
        return onsets
    hop = 256
    spec = np.abs(librosa.stft(np.asarray(y, dtype=float), n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=float(sr), n_fft=2048)
    band = (freqs >= 50.0) & (freqs <= 1800.0)
    onset_env = librosa.onset.onset_strength(S=spec[band, :], sr=float(sr), hop_length=hop)
    times = librosa.frames_to_time(np.arange(len(onset_env)), sr=sr, hop_length=hop)
    half = 0.45 * tick
    win = min(0.06, 0.25 * tick)
    floor = 0.10 * float(np.percentile(onset_env, 90) + 1e-9)

    def at(t: float) -> float:
        idx = int(np.clip(np.searchsorted(times, t), 0, len(onset_env) - 1))
        return float(onset_env[idx])

    def peak_near(t: float) -> float:
        mask = (times >= t - win) & (times <= t + win)
        if not np.any(mask):
            return at(t)
        return float(np.max(onset_env[mask]))

    kept: list[float] = []
    for onset in np.atleast_1d(onsets).astype(float):
        peak = peak_near(onset)
        trough = at(onset - half)
        if peak >= 1.35 * max(trough, 1e-6) and peak >= floor:
            kept.append(float(onset))
    return np.asarray(kept, dtype=float)


def merge_unconfirmed_repeats(
    y: np.ndarray,
    sr: int | float,
    notes: list[NoteEvent],
    tick: float,
    *,
    ratio: float = 1.12,
    max_gap: float = 0.06,
) -> list[NoteEvent]:
    """Glue fragments cut on f0 wobble or envelope shimmer, not a pluck.

    Split stays strict; merge is timid. Any RMS re-peak ≥ 1.12× keeps an
    8th-note attack. Only dead shimmer and sub-100 ms ±1 jitter get glued.
    """
    import librosa

    if len(notes) < 2:
        return list(notes)
    hop = 256
    rms = librosa.feature.rms(y=y, hop_length=hop, frame_length=512)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    half = 0.45 * tick
    win = min(0.06, 0.25 * tick)

    def at(t: float) -> float:
        idx = int(np.clip(np.searchsorted(times, t), 0, len(rms) - 1))
        return float(rms[idx])

    def peak_near(t: float) -> float:
        mask = (times >= t - win) & (times <= t + win)
        if not np.any(mask):
            return at(t)
        return float(np.max(rms[mask]))

    def is_pluck(t: float) -> bool:
        return peak_near(t) >= ratio * max(at(t - half), 1e-6)

    ordered = sorted(notes, key=lambda n: n.start)
    merged: list[NoteEvent] = [ordered[0]]
    for note in ordered[1:]:
        prev = merged[-1]
        gap = note.start - prev.end
        close_pitch = note.pitch == prev.pitch
        short_jitter = (
            abs(note.pitch - prev.pitch) <= 1
            and min(note.duration, prev.duration) < 0.10
        )
        if (close_pitch or short_jitter) and gap <= max_gap and not is_pluck(note.start):
            pitch = note.pitch if note.duration > prev.duration else prev.pitch
            merged[-1] = NoteEvent(
                start=prev.start,
                end=max(prev.end, note.end),
                pitch=pitch,
                amplitude=max(prev.amplitude, note.amplitude),
            )
        else:
            merged.append(note)
    return merged


def split_repeated_pitches(
    y: np.ndarray,
    sr: int | float,
    notes: list[NoteEvent],
    bpm: float,
    grid: str = "8",
    min_duration: float = MIN_NOTE_DURATION_S,
) -> list[NoteEvent]:
    """Same-pitch repeats: confirmed pluck onsets, then meter on long holds."""
    from base_sheet.rhythm import seconds_per_tick

    tick = seconds_per_tick(bpm, grid)
    onsets = detect_bass_onsets(y, sr, bpm=bpm)
    onsets = _nms_times(onsets, max(0.09, 0.42 * tick))
    onsets = _confirmed_reattacks(y, sr, onsets, tick)
    split = _seed_holes_at_onsets(notes, onsets, tick, y=y, sr=sr)
    split = split_at_onsets(split, onsets, min_duration=min_duration)
    long: list[NoteEvent] = []
    short: list[NoteEvent] = []
    for note in split:
        if note.duration >= 1.45 * tick:
            long.append(note)
        else:
            short.append(note)
    if long:
        long = split_repeats_on_meter(y, sr, long, bpm, grid)
    out = sorted(short + long, key=lambda n: n.start)
    return merge_unconfirmed_repeats(y, sr, out, tick)


def stamp_amplitudes(
    y: np.ndarray,
    sr: int | float,
    notes: list[NoteEvent],
) -> list[NoteEvent]:
    """Set velocity-like amplitude from RMS at each onset."""
    import librosa

    if not notes:
        return []
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    peak = float(np.percentile(rms, 95) + 1e-9)
    stamped: list[NoteEvent] = []
    for note in notes:
        idx = int(np.clip(np.searchsorted(times, note.start), 0, len(rms) - 1))
        amp = float(np.clip(rms[idx] / peak, 0.15, 1.0))
        stamped.append(
            NoteEvent(start=note.start, end=note.end, pitch=note.pitch, amplitude=amp)
        )
    return stamped
