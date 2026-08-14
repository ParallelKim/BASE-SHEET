"""Render transcribed notes to WAV so you can listen without a DAW."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from base_sheet.models import NoteEvent


def render_notes(
    notes: list[NoteEvent],
    sr: int,
    duration: float | None = None,
) -> np.ndarray:
    """Simple plucked-bass synth (fundamental + 2nd harmonic, decaying)."""
    if duration is None:
        duration = max((n.end for n in notes), default=0.0) + 0.25
    n_samples = max(1, int(np.ceil(float(duration) * sr)))
    y = np.zeros(n_samples, dtype=np.float32)
    two_pi = 2.0 * np.pi
    for note in notes:
        start = max(0, int(note.start * sr))
        end = min(n_samples, int(note.end * sr))
        if end - start < 8:
            continue
        freq = 440.0 * (2.0 ** ((int(note.pitch) - 69) / 12.0))
        t = np.arange(end - start, dtype=np.float32) / float(sr)
        env = (1.0 - np.exp(-t * 90.0)) * np.exp(-t * 3.2)
        wave = np.sin(two_pi * freq * t) + 0.4 * np.sin(two_pi * 2.0 * freq * t)
        y[start:end] += float(note.amplitude) * env * wave.astype(np.float32)
    peak = float(np.max(np.abs(y))) + 1e-9
    return np.clip(y * (0.85 / peak), -1.0, 1.0)


def write_wav(path: Path, y: np.ndarray, sr: int) -> Path:
    import soundfile as sf

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), y, int(sr), subtype="PCM_16")
    return path


def write_previews(
    stem: np.ndarray,
    sr: int,
    notes: list[NoteEvent],
    out_dir: str | Path,
    name: str,
) -> dict[str, Path]:
    """Synth-only preview, plus L=stem / R=MIDI stereo compare."""
    out = Path(out_dir)
    n = len(stem)
    synth = render_notes(notes, int(sr), duration=n / float(sr))
    if len(synth) < n:
        synth = np.pad(synth, (0, n - len(synth)))
    synth = synth[:n]
    peak_s = float(np.max(np.abs(stem))) + 1e-9
    left = np.clip(stem / peak_s * 0.85, -1.0, 1.0)
    stereo = np.stack([left, synth], axis=1)
    preview = write_wav(out / f"{name}.preview.wav", synth, int(sr))
    compare = write_wav(out / f"{name}.compare.wav", stereo, int(sr))
    return {"preview": preview, "compare": compare}
