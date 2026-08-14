from base_sheet.correct import fold_to_bass_range
from base_sheet.rhythm import parse_key_string, snap_to_key
from base_sheet.models import QuantizedNote


def test_fold_high_harmonic_into_bass_range():
    assert fold_to_bass_range(52) == 52
    assert fold_to_bass_range(80) == 56  # 80-12-12


def test_snap_c_sharp_in_c_major_moves():
    notes = [QuantizedNote(0.0, 1.0, 61, 80)]  # C#4
    out = snap_to_key(notes, "C major")
    assert out[0].pitch % 12 != 1 or out[0].pitch != 61
    assert out[0].pitch % 12 in {0, 2}  # C or D


def test_parse_em():
    k = parse_key_string("Em")
    assert k.mode == "minor"
