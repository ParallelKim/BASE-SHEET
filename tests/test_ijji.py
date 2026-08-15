from pathlib import Path

import pytest

from base_sheet.pipeline import run
from ijji_eval import fixture_path, score_notes
from ijji_truth import SCORE_BPM, SCORE_KEY


@pytest.mark.slow
def test_ijji_verse_roots_match_published_tab(tmp_path: Path):
    """자우림 「잊지」 출판 탭: q=84, F# minor, 버스 13–24 루트."""
    stem = fixture_path()
    if stem is None:
        pytest.skip("place tests/fixtures/ijji_bass.m4a or the uploaded stem")
    result = run(
        stem,
        tmp_path,
        engine="crepe",
        bpm=SCORE_BPM,
        grid="8",
        key=SCORE_KEY,
        write_preview=False,
    )
    listen = None if result.listen is None else result.listen.pitch_within_semitone
    metrics = score_notes(result.performed, bpm=SCORE_BPM, listen_within=listen)
    assert metrics.verse_acc >= 0.80
    assert metrics.chorus_acc >= 0.50
    if listen is not None:
        assert listen >= 0.65
