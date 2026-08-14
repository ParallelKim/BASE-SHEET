from pathlib import Path

from base_sheet.models import QuantizedNote
from base_sheet.notate import build_score, write_score


def test_score_uses_bass_clef_and_pitch(tmp_path: Path):
    notes = [QuantizedNote(offset_ql=0.0, duration_ql=1.0, pitch=40, velocity=80)]
    xml = write_score(notes, tmp_path, "probe", bpm=120.0)["musicxml"]
    text = xml.read_text(encoding="utf-8")
    assert "<clef>" in text and "<sign>F</sign>" in text
    assert "<step>E</step>" in text


def test_midi_has_no_pitch_bends(tmp_path: Path):
    import pretty_midi

    notes = [QuantizedNote(offset_ql=0.0, duration_ql=1.0, pitch=40, velocity=80)]
    midi_path = write_score(notes, tmp_path, "probe", bpm=100.0)["midi"]
    pm = pretty_midi.PrettyMIDI(str(midi_path))
    assert pm.instruments[0].program == 33
    assert pm.instruments[0].pitch_bends == []
    assert pm.instruments[0].notes[0].pitch == 40


def test_build_score_title():
    score = build_score(
        [QuantizedNote(0.0, 1.0, 45, 70)],
        bpm=90,
        title="Antifreeze",
    )
    assert score.metadata.title == "Antifreeze"
