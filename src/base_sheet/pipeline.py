"""Isolated (or leaky) bass stem → MIDI / MusicXML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from base_sheet import listen, notate, rhythm, segment, transcribe
from base_sheet.audio import load_mono
from base_sheet.listen import ListenScore
from base_sheet.models import MIN_NOTE_DURATION_S, NoteEvent, QuantizedNote


@dataclass
class PipelineResult:
    bpm: float
    time_signature: str
    key: str
    note_count: int
    engine: str
    midi_path: Path
    quantized_midi_path: Path
    musicxml_path: Path
    notes: list[QuantizedNote]
    performed: list[NoteEvent]
    listen: ListenScore | None


def run(
    audio_path: str | Path,
    out_dir: str | Path,
    *,
    bpm: float | None = None,
    time_signature: str = "4/4",
    engine: str = "crepe",
    grid: str = "8",
    key: str | None = None,
    snap_key: bool = False,
    min_duration: float = MIN_NOTE_DURATION_S,
    events: list[NoteEvent] | None = None,
) -> PipelineResult:
    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    y, sr = load_mono(path)
    used_bpm = float(bpm) if bpm is not None else rhythm.estimate_bpm(y, sr)
    raw_notes = (
        events
        if events is not None
        else transcribe.transcribe(
            path, y, int(sr), engine=engine, min_duration=min_duration
        )
    )
    raw_notes = segment.split_repeats_on_meter(y, sr, raw_notes, used_bpm, grid)
    raw_notes = segment.stamp_amplitudes(y, sr, raw_notes)
    raw_notes = rhythm.make_monophonic(raw_notes)

    out = Path(out_dir)
    midi_path = notate.write_performance_midi(
        raw_notes, out / f"{path.stem}.mid", used_bpm
    )

    quantized = rhythm.quantize(raw_notes, used_bpm, grid=grid)
    key_hint = key
    if snap_key:
        if key_hint is None:
            tmp = notate.build_score(quantized, used_bpm, time_signature, title=path.stem)
            key_hint = notate.key_name(tmp)
        quantized = rhythm.snap_to_key(quantized, key_hint)

    written = notate.write_score(
        quantized,
        out_dir,
        path.stem,
        bpm=used_bpm,
        time_signature=time_signature,
        key_hint=key_hint,
    )
    displayed_key = (
        str(rhythm.parse_key_string(key_hint)) if key_hint else notate.key_name(written["score"])
    )
    listen_score = listen.score_listen(y, sr, raw_notes)
    return PipelineResult(
        bpm=used_bpm,
        time_signature=time_signature,
        key=displayed_key,
        note_count=len(raw_notes),
        engine=engine,
        midi_path=midi_path,
        quantized_midi_path=written["midi"],
        musicxml_path=written["musicxml"],
        notes=quantized,
        performed=raw_notes,
        listen=listen_score,
    )
