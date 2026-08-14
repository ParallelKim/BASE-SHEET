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
_CREPE_SR = 16000


def _times_like(n_frames: int, sr: float, hop_length: int) -> np.ndarray:
    import librosa

    return librosa.times_like(np.zeros(n_frames), sr=sr, hop_length=hop_length)


def _pyin_frame_length(sr: int) -> int:
    """≥ ~4 periods of E1 so pYIN can track the bass fundamental."""
    period = float(sr) / _BASS_FMIN_HZ
    needed = max(2048, int(4.0 * period))
    return int(2 ** np.ceil(np.log2(needed)))


def _f0_torchcrepe(y: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray, int, int] | None:
    try:
        import librosa
        import torch
        import torchcrepe
    except ImportError:
        return None

    if int(sr) != _CREPE_SR:
        y = librosa.resample(np.asarray(y, dtype=float), orig_sr=int(sr), target_sr=_CREPE_SR)
        sr = _CREPE_SR
    hop = 160  # 10 ms at CREPE's native 16 kHz
    audio = torch.tensor(np.asarray(y, dtype=np.float32), dtype=torch.float32).unsqueeze(0)
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    decoder = getattr(torchcrepe.decode, "viterbi", None)
    kwargs = dict(
        hop_length=hop,
        fmin=_BASS_FMIN_HZ,
        fmax=_BASS_FMAX_HZ,
        model="full",
        return_periodicity=True,
        device=device,
        batch_size=2048,
        pad=True,
    )
    if decoder is not None:
        kwargs["decoder"] = decoder
    pitch, periodicity = torchcrepe.predict(audio, sr, **kwargs)
    pitch_np = pitch.detach().cpu().numpy().reshape(-1)
    per_np = periodicity.detach().cpu().numpy().reshape(-1)
    import scipy.ndimage

    per_np = scipy.ndimage.median_filter(per_np, size=3)
    pitch_np[~np.isfinite(pitch_np)] = 0.0
    return pitch_np, per_np, hop, sr


def _f0_pyin(y: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray, int, int]:
    import librosa

    hop = 256
    frame_length = _pyin_frame_length(int(sr))
    f0, _voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=_BASS_FMIN_HZ,
        fmax=_BASS_FMAX_HZ,
        sr=sr,
        hop_length=hop,
        frame_length=frame_length,
        fill_na=np.nan,
    )
    conf = np.nan_to_num(np.asarray(voiced_probs, dtype=float), nan=0.0)
    return np.asarray(f0, dtype=float), conf, hop, int(sr)


def transcribe_crepe(
    y: np.ndarray,
    sr: int,
    *,
    min_duration: float = MIN_NOTE_DURATION_S,
) -> list[NoteEvent]:
    """CREPE Notes segmentation on a torchcrepe or pYIN contour."""
    import librosa

    packed = _f0_torchcrepe(y, int(sr))
    if packed is None:
        target_sr = 22050
        y_f0 = y
        f0_sr = int(sr)
        if f0_sr != target_sr:
            y_f0 = librosa.resample(y, orig_sr=f0_sr, target_sr=target_sr)
            f0_sr = target_sr
        f0_hz, confidence, hop, used_sr = _f0_pyin(y_f0, f0_sr)
        floor = 0.10
    else:
        f0_hz, confidence, hop, used_sr = packed
        floor = CREPE_PERIODICITY_FLOOR

    midi = np.full(f0_hz.shape, UNVOICED, dtype=int)
    valid = np.isfinite(f0_hz) & (f0_hz > 0)
    midi[valid] = np.rint(librosa.hz_to_midi(f0_hz[valid])).astype(int)
    midi = correct.correct_contour(midi, confidence, confidence_floor=floor)
    times = _times_like(len(midi), float(used_sr), hop)
    notes = segment.contour_to_notes(midi, confidence, times, min_duration=min_duration)
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
