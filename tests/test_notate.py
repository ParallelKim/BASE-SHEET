from pathlib import Path

from base_sheet.models import NoteEvent, QuantizedNote
from base_sheet.notate import build_score, write_performance_midi, write_score


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


def test_performance_midi_keeps_wall_clock(tmp_path: Path):
    import pretty_midi

    notes = [NoteEvent(0.70, 0.93, 35, 0.8), NoteEvent(0.93, 1.16, 35, 0.7)]
    path = write_performance_midi(notes, tmp_path / "listen.mid", bpm=128.0)
    pm = pretty_midi.PrettyMIDI(str(path))
    got = pm.instruments[0].notes
    assert abs(got[0].start - 0.70) < 0.01
    assert got[0].end < got[1].start  # retrigger gap
    assert got[0].pitch == 35
