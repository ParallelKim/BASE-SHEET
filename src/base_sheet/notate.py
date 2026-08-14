"""Bass-clef MusicXML (music21) and GM-bass MIDI (pretty_midi, no pitch bends)."""

from __future__ import annotations

from pathlib import Path

from music21 import clef, instrument, key, metadata, meter, note, stream, tempo

from base_sheet.models import GM_ELECTRIC_BASS_FINGER, QuantizedNote


def parse_time_signature(value: str) -> meter.TimeSignature:
    return meter.TimeSignature(value.strip())


def build_score(
    notes: list[QuantizedNote],
    bpm: float,
    time_signature: str = "4/4",
    title: str = "Bass",
    key_hint: str | None = None,
) -> stream.Score:
    part = stream.Part(id="Bass")
    part.insert(0, instrument.ElectricBass())
    part.insert(0, clef.BassClef())
    part.insert(0, parse_time_signature(time_signature))
    part.insert(0, tempo.MetronomeMark(number=float(bpm)))

    for qn in notes:
        n = note.Note()
        n.pitch.midi = qn.pitch
        n.quarterLength = qn.duration_ql
        n.volume.velocity = qn.velocity
        part.insert(qn.offset_ql, n)

    part.makeRests(fillGaps=True, inPlace=True)
    part.makeMeasures(inPlace=True)
    part.makeTies(inPlace=True)

    if key_hint:
        from base_sheet.rhythm import parse_key_string

        part.insert(0, parse_key_string(key_hint))
    else:
        analyzed = part.analyze("key")
        if isinstance(analyzed, key.Key):
            part.insert(0, analyzed)

    score = stream.Score()
    score.insert(0, metadata.Metadata())
    score.metadata.title = title
    score.insert(0, part)
    return score


def write_midi(notes: list[QuantizedNote], path: Path, bpm: float) -> Path:
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(initial_tempo=float(bpm))
    inst = pretty_midi.Instrument(program=GM_ELECTRIC_BASS_FINGER, name="Bass")
    quarter = 60.0 / float(bpm)
    for qn in notes:
        start = qn.offset_ql * quarter
        end = start + qn.duration_ql * quarter
        inst.notes.append(
            pretty_midi.Note(
                velocity=int(qn.velocity),
                pitch=int(qn.pitch),
                start=start,
                end=end,
            )
        )
    pm.instruments.append(inst)
    pm.remove_invalid_notes()
    path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(path))
    return path


def write_score(
    notes: list[QuantizedNote],
    out_dir: str | Path,
    stem: str,
    bpm: float,
    time_signature: str = "4/4",
    key_hint: str | None = None,
) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    score = build_score(
        notes, bpm=bpm, time_signature=time_signature, title=stem, key_hint=key_hint
    )
    midi_path = out / f"{stem}.mid"
    xml_path = out / f"{stem}.musicxml"
    write_midi(notes, midi_path, bpm)
    score.write("musicxml", fp=str(xml_path))
    return {"midi": midi_path, "musicxml": xml_path, "score": score}


def key_name(score: stream.Score) -> str:
    return str(score.analyze("key"))
