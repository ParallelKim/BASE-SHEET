"""Tempo voting, grid quantization, same-pitch merge, optional key snap.

BPM voting follows BassLift (multiple librosa start_bpm hints + beat_track).
Grid names 8/16/8t/16t follow BassLift. Adjacent same-pitch merge follows
BassLift plus instrument-agnostic-amt bass_v2 (avoid over-segmentation).
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from base_sheet.models import NoteEvent, QuantizedNote

DEFAULT_BPM = 120.0
MIN_DURATION_TICKS = 1

# ticks per quarter note
GRID_TICKS = {
    "8": 2,
    "16": 4,
    "8t": 3,
    "16t": 6,
}


def estimate_bpm(y: np.ndarray, sr: int | float) -> float:
    """Vote across several tempo priors (BassLift). Fallback 120."""
    import librosa

    candidates: list[float] = []
    for start_bpm in (80, 100, 120, 140, 160):
        try:
            tempo_arr = librosa.feature.tempo(y=y, sr=sr, start_bpm=float(start_bpm))
            if len(tempo_arr) > 0:
                candidates.append(float(np.atleast_1d(tempo_arr)[0]))
        except Exception:
            continue
    try:
        tempo_bt, _beats = librosa.beat.beat_track(y=y, sr=sr)
        candidates.append(float(np.atleast_1d(tempo_bt)[0]))
    except Exception:
        pass
    candidates = [c for c in candidates if np.isfinite(c) and 40 <= c <= 300]
    if not candidates:
        return DEFAULT_BPM
    rounded = [int(round(c)) for c in candidates]
    return float(Counter(rounded).most_common(1)[0][0])


def ticks_per_quarter(grid: str) -> int:
    key = grid.strip().lower()
    if key not in GRID_TICKS:
        raise ValueError(f"Unknown grid {grid!r}; expected one of {sorted(GRID_TICKS)}")
    return GRID_TICKS[key]


def seconds_per_tick(bpm: float, grid: str) -> float:
    if bpm <= 0:
        raise ValueError("bpm must be positive")
    return (60.0 / bpm) / ticks_per_quarter(grid)


def time_to_tick(seconds: float, bpm: float, grid: str) -> int:
    return max(0, int(round(seconds / seconds_per_tick(bpm, grid))))


def make_monophonic(notes: list[NoteEvent]) -> list[NoteEvent]:
    if not notes:
        return []
    ordered = sorted(notes, key=lambda n: (n.start, -n.amplitude, n.pitch))
    clipped: list[NoteEvent] = []
    for note in ordered:
        if clipped and note.start < clipped[-1].end:
            prev = clipped[-1]
            new_end = min(prev.end, note.start)
            if new_end > prev.start:
                clipped[-1] = NoteEvent(
                    start=prev.start,
                    end=new_end,
                    pitch=prev.pitch,
                    amplitude=prev.amplitude,
                )
            else:
                clipped.pop()
        if note.end > note.start:
            clipped.append(note)
    return clipped


def amplitude_to_velocity(amplitude: float) -> int:
    return int(max(30, min(127, round(float(amplitude) * 127))))


def quantize(
    notes: list[NoteEvent],
    bpm: float,
    *,
    grid: str = "16",
    monophonic: bool = True,
) -> list[QuantizedNote]:
    """Snap onsets/durations to the chosen grid."""
    source = make_monophonic(notes) if monophonic else list(notes)
    tpq = ticks_per_quarter(grid)
    quantized: list[QuantizedNote] = []
    seen_onsets: dict[int, int] = {}

    for note in source:
        start_tick = time_to_tick(note.start, bpm, grid)
        end_tick = time_to_tick(note.end, bpm, grid)
        dur_ticks = max(MIN_DURATION_TICKS, end_tick - start_tick)
        velocity = amplitude_to_velocity(note.amplitude)
        if start_tick in seen_onsets:
            idx = seen_onsets[start_tick]
            existing = quantized[idx]
            if velocity >= existing.velocity:
                quantized[idx] = QuantizedNote(
                    offset_ql=start_tick / tpq,
                    duration_ql=dur_ticks / tpq,
                    pitch=note.pitch,
                    velocity=velocity,
                )
            continue
        seen_onsets[start_tick] = len(quantized)
        quantized.append(
            QuantizedNote(
                offset_ql=start_tick / tpq,
                duration_ql=dur_ticks / tpq,
                pitch=note.pitch,
                velocity=velocity,
            )
        )

    quantized.sort(key=lambda n: (n.offset_ql, n.pitch))
    grid_ql = 1.0 / tpq
    return merge_same_pitch(quantized, min_keep_ql=grid_ql)


def merge_same_pitch(
    notes: list[QuantizedNote],
    gap_ql: float = 1e-6,
    min_keep_ql: float = 0.25,
) -> list[QuantizedNote]:
    """Glue only sub-grid fragments of the same pitch.

    Full-length repeated attacks (e.g. eight B eighth-notes in Antifreeze)
    must stay separate. BassLift's merge was meant for quantization splits,
    not musical repeats.
    """
    if not notes:
        return []
    out = [notes[0]]
    for note in notes[1:]:
        prev = out[-1]
        prev_end = prev.offset_ql + prev.duration_ql
        debris = prev.duration_ql < min_keep_ql - 1e-9 or note.duration_ql < min_keep_ql - 1e-9
        if (
            debris
            and note.pitch == prev.pitch
            and note.offset_ql <= prev_end + gap_ql
        ):
            new_end = max(prev_end, note.offset_ql + note.duration_ql)
            out[-1] = QuantizedNote(
                offset_ql=prev.offset_ql,
                duration_ql=new_end - prev.offset_ql,
                pitch=prev.pitch,
                velocity=max(prev.velocity, note.velocity),
            )
        else:
            out.append(note)
    return out


def parse_key_string(text: str):
    from music21 import key

    raw = text.strip()
    lower = raw.lower()
    if "min" in lower:
        tonic = raw.replace("minor", "").replace("Minor", "").replace("min", "").strip()
        return key.Key(tonic[0].upper() + tonic[1:] if tonic else "C", "minor")
    if "maj" in lower:
        tonic = (
            raw.replace("major", "")
            .replace("Major", "")
            .replace("maj", "")
            .strip()
        )
        return key.Key(tonic or "C", "major")
    if raw.endswith("m") and len(raw) <= 3:
        return key.Key(raw[:-1], "minor")
    return key.Key(raw)


def snap_to_key(notes: list[QuantizedNote], key_text: str) -> list[QuantizedNote]:
    """NeuralNote-style scale quantize: nearest diatonic pitch class."""
    k = parse_key_string(key_text)
    pcs = {p.pitchClass for p in k.getPitches("C1", "C8")}
    snapped: list[QuantizedNote] = []
    for note in notes:
        pc = note.pitch % 12
        if pc in pcs:
            snapped.append(note)
            continue
        best = 0
        best_d = 99
        for delta in range(-2, 3):
            if delta == 0:
                continue
            if (pc + delta) % 12 in pcs and abs(delta) < best_d:
                best, best_d = delta, abs(delta)
        snapped.append(
            QuantizedNote(
                offset_ql=note.offset_ql,
                duration_ql=note.duration_ql,
                pitch=note.pitch + best,
                velocity=note.velocity,
            )
        )
    return snapped
