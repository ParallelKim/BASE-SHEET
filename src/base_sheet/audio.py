"""Load mono audio, including m4a via ffmpeg when libsndfile cannot."""

from __future__ import annotations

import io
import subprocess
from pathlib import Path

import numpy as np


def load_mono(path: str | Path) -> tuple[np.ndarray, int]:
    import librosa
    import soundfile as sf

    p = Path(path)
    try:
        y, sr = librosa.load(str(p), sr=None, mono=True)
        return np.asarray(y, dtype=np.float32), int(sr)
    except Exception:
        pass

    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(p),
            "-f",
            "wav",
            "-acodec",
            "pcm_f32le",
            "-ac",
            "1",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    y, sr = sf.read(io.BytesIO(proc.stdout), dtype="float32")
    if y.ndim > 1:
        y = np.mean(y, axis=1)
    return np.asarray(y, dtype=np.float32), int(sr)
