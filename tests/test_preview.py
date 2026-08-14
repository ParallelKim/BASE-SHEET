from pathlib import Path

import numpy as np

from base_sheet.models import NoteEvent
from base_sheet.preview import render_notes, write_previews


def test_render_notes_has_energy_at_midi_pitch():
    sr = 22050
    notes = [NoteEvent(0.05, 0.4, 40, 0.9)]
    y = render_notes(notes, sr, duration=0.5)
    spec = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    freqs = np.fft.rfftfreq(len(y), 1 / sr)
    f0 = 440.0 * (2.0 ** ((40 - 69) / 12.0))
    band = (freqs >= f0 * 0.9) & (freqs <= f0 * 1.1)
    assert spec[band].max() > spec.max() * 0.2


def test_write_previews_stereo_compare(tmp_path: Path):
    sr = 8000
    stem = np.zeros(sr, dtype=np.float32)
    stem[100:400] = 0.4
    notes = [NoteEvent(0.05, 0.3, 35, 0.8)]
    paths = write_previews(stem, sr, notes, tmp_path, "probe")
    import soundfile as sf

    synth, ssr = sf.read(paths["preview"])
    cmp, csr = sf.read(paths["compare"])
    assert ssr == sr and csr == sr
    assert synth.ndim == 1
    assert cmp.ndim == 2 and cmp.shape[1] == 2
    assert np.max(np.abs(synth)) > 0.1
