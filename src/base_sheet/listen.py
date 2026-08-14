"""Compare transcribed MIDI to the bass audio (listening fidelity)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from base_sheet.models import NoteEvent


@dataclass
class ListenScore:
    """Frame-wise agreement between audio f0 and MIDI notes."""

    voiced_frames: int
    pitch_within_semitone: float
    chroma_cosine: float


def _active_midi(notes: list[NoteEvent], times: np.ndarray) -> np.ndarray:
    out = np.full(len(times), np.nan)
    for note in notes:
        mask = (times >= note.start) & (times < note.end)
        out[mask] = float(note.pitch)
    return out


def score_listen(y: np.ndarray, sr: int | float, notes: list[NoteEvent]) -> ListenScore:
    """How closely MIDI tracks the stem: pYIN vs MIDI, plus chroma cosine."""
    import librosa

    hop = 512
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=41.2,
        fmax=392.0,
        sr=sr,
        hop_length=hop,
        frame_length=4096,
        fill_na=np.nan,
    )
    times = librosa.times_like(f0, sr=sr, hop_length=hop)
    midi = _active_midi(notes, times)
    f0_midi = np.full_like(f0, np.nan, dtype=float)
    valid = np.isfinite(f0) & (f0 > 0)
    f0_midi[valid] = librosa.hz_to_midi(f0[valid])
    voiced = valid & np.isfinite(midi) & (np.nan_to_num(voiced_probs) > 0.2)
    n = int(voiced.sum())
    if n == 0:
        pitch_hit = 0.0
    else:
        pitch_hit = float(np.mean(np.abs(f0_midi[voiced] - midi[voiced]) <= 1.0))

    chroma_a = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop, fmin=32.7)
    chroma_m = np.zeros_like(chroma_a)
    for i, t in enumerate(times[: chroma_a.shape[1]]):
        hits = [n.pitch % 12 for n in notes if n.start <= t < n.end]
        for pc in hits:
            chroma_m[pc, i] = 1.0
    n_ch = min(chroma_a.shape[1], chroma_m.shape[1])
    a = chroma_a[:, :n_ch]
    m = chroma_m[:, :n_ch]
    energy = np.linalg.norm(a, axis=0) * np.linalg.norm(m, axis=0)
    active = energy > 1e-6
    if not np.any(active):
        cosine = 0.0
    else:
        dots = np.sum(a[:, active] * m[:, active], axis=0)
        denom = np.linalg.norm(a[:, active], axis=0) * np.linalg.norm(m[:, active], axis=0)
        cosine = float(np.mean(dots / np.maximum(denom, 1e-9)))
    return ListenScore(
        voiced_frames=n,
        pitch_within_semitone=pitch_hit,
        chroma_cosine=cosine,
    )
