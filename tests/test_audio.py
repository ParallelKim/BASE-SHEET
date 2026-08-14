from pathlib import Path

from base_sheet.audio import load_mono

FIXTURE = Path(__file__).parent / "fixtures" / "Antifreeze_bass_mixed.m4a"


def test_antifreeze_m4a_loads_via_ffmpeg():
    y, sr = load_mono(FIXTURE)
    assert sr > 0
    assert y.size > sr  # longer than one second
    assert y.ndim == 1
