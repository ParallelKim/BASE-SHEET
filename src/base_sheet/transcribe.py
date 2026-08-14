"""f0 / note engines: CREPE-style contour (default) or Basic Pitch."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from base_sheet import correct, segment
from base_sheet.models import (
    BASS_MIDI_MAX,
    BASS_MIDI_MIN,
    CREPE_PERIODICITY_FLOOR,
    MIN_NOTE_DURATION_S,
    UNVOICED,
    NoteEvent,
)

_BASS_FMIN_HZ = 41.2
_BASS_FMAX_HZ = 392.0


def _times_like(n_frames: int, sr: float, hop_length: int) -> np.ndarray:
    import librosa

    return librosa.times_like(np.zeros(n_frames), sr=sr, hop_length=hop_length)


def _f0_torchcrepe(y: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray, int] | None:
    try:
        import torch
        import torchcrepe
    except ImportError:
        return None

    hop = int(sr * 0.010)
    audio = torch.tensor(y, dtype=torch.float32).unsqueeze(0)
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    pitch, periodicity = torchcrepe.predict(
        audio,
        sr,
        hop_length=hop,
        fmin=_BASS_FMIN_HZ,
        fmax=_BASS_FMAX_HZ,
        model="full",
        return_periodicity=True,
        device=device,
        batch_size=2048,
    )
    pitch_np = pitch.detach().cpu().numpy().reshape(-1)
    per_np = periodicity.detach().cpu().numpy().reshape(-1)
    import scipy.ndimage

    per_np = scipy.ndimage.median_filter(per_np, size=3)
    return pitch_np, per_np, hop


def _f0_pyin(y: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray, int]:
    import librosa

    hop = 512
    f0, _voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=_BASS_FMIN_HZ,
        fmax=_BASS_FMAX_HZ,
        sr=sr,
        hop_length=hop,
        fill_na=np.nan,
    )
    conf = np.nan_to_num(np.asarray(voiced_probs, dtype=float), nan=0.0)
    return np.asarray(f0, dtype=float), conf, hop


def transcribe_crepe(
    y: np.ndarray,
    sr: int,
    *,
    min_duration: float = MIN_NOTE_DURATION_S,
) -> list[NoteEvent]:
    """CREPE Notes segmentation on a torchcrepe or pYIN contour."""
    import librosa

    target_sr = 22050
    if int(sr) != target_sr:
        y = librosa.resample(y, orig_sr=int(sr), target_sr=target_sr)
        sr = target_sr

    packed = _f0_torchcrepe(y, int(sr))
    if packed is None:
        f0_hz, confidence, hop = _f0_pyin(y, int(sr))
        floor = 0.10
    else:
        f0_hz, confidence, hop = packed
        floor = CREPE_PERIODICITY_FLOOR

    midi = np.full(f0_hz.shape, UNVOICED, dtype=int)
    valid = np.isfinite(f0_hz) & (f0_hz > 0)
    midi[valid] = np.rint(librosa.hz_to_midi(f0_hz[valid])).astype(int)
    midi = correct.correct_contour(midi, confidence, confidence_floor=floor)
    times = _times_like(len(midi), float(sr), hop)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    if len(rms) < len(midi):
        rms = np.pad(rms, (0, len(midi) - len(rms)))
    rms = rms[: len(midi)]
    peak = float(np.percentile(rms, 95) + 1e-9)
    amps = np.clip(rms / peak, 0.05, 1.0)

    notes = segment.contour_to_notes(
        midi, confidence, times, min_duration=min_duration, amplitudes=amps
    )
    return correct.drop_short_notes(notes, min_duration)


def transcribe_basic_pitch(
    audio_path: str | Path,
    y: np.ndarray,
    sr: int,
    *,
    min_duration: float = MIN_NOTE_DURATION_S,
) -> list[NoteEvent]:
    """Basic Pitch notes, no pitch-bends, then the same bass corrections."""
    from basic_pitch.inference import predict

    _model_output, _midi, raw_events = predict(
        str(audio_path),
        minimum_frequency=_BASS_FMIN_HZ,
        maximum_frequency=_BASS_FMAX_HZ,
    )
    notes: list[NoteEvent] = []
    for item in raw_events:
        start, end, pitch = float(item[0]), float(item[1]), int(item[2])
        amplitude = float(item[3]) if len(item) > 3 else 0.8
        folded = correct.fold_to_bass_range(pitch)
        if folded is None or end <= start:
            continue
        notes.append(NoteEvent(start=start, end=end, pitch=folded, amplitude=amplitude))
    notes.sort(key=lambda n: (n.start, n.pitch))
    return correct.drop_short_notes(notes, min_duration)


def transcribe(
    audio_path: str | Path,
    y: np.ndarray,
    sr: int,
    *,
    engine: str = "crepe",
    min_duration: float = MIN_NOTE_DURATION_S,
) -> list[NoteEvent]:
    name = engine.strip().lower()
    if name in {"crepe", "crepe-notes", "pyin"}:
        return transcribe_crepe(y, sr, min_duration=min_duration)
    if name in {"basic-pitch", "basic_pitch"}:
        return transcribe_basic_pitch(audio_path, y, sr, min_duration=min_duration)
    raise ValueError(f"Unknown engine {engine!r}")


# Re-export for tests that imported fold from transcribe.
fold_to_bass_range = correct.fold_to_bass_range
BASS_MIDI_MIN = BASS_MIDI_MIN
BASS_MIDI_MAX = BASS_MIDI_MAX
