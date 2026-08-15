"""Score BASE-SHEET against the published 「있지」 bass tab."""

from __future__ import annotations

from pathlib import Path

from ijji_truth import SCORE_BPM, played_hits
from song_score import SongScore, score_song
from base_sheet.models import NoteEvent

UPLOAD_STEM = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "______-________-bass-F__minor-84bpm-440hz_9aa2.m4a"
)
FIXTURE = Path(__file__).parent / "fixtures" / "ijji_bass.m4a"


def fixture_path() -> Path | None:
    if FIXTURE.is_file():
        return FIXTURE
    if UPLOAD_STEM.is_file():
        return UPLOAD_STEM
    return None


def score_ijji(notes: list[NoteEvent], *, bpm: float = SCORE_BPM) -> SongScore:
    from ijji_truth import SECTIONS

    return score_song(notes, played_hits(), bpm, SECTIONS)
