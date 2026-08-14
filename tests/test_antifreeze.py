from pathlib import Path

import pytest

from base_sheet.pipeline import run

FIXTURE = Path(__file__).parent / "fixtures" / "Antifreeze_bass_mixed.m4a"


@pytest.mark.slow
def test_antifreeze_stem_writes_midi_and_musicxml(tmp_path: Path):
    """Leaky separated stem; just assert the pipeline completes."""
    if not FIXTURE.is_file():
        pytest.skip("fixture missing")
    result = run(FIXTURE, tmp_path, engine="crepe")
    assert result.note_count >= 1
    assert result.midi_path.is_file()
    assert result.musicxml_path.is_file()
    text = result.musicxml_path.read_text(encoding="utf-8")
    assert "<sign>F</sign>" in text
