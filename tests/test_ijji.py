from pathlib import Path

import pytest

from base_sheet.pipeline import run
from ijji_eval import fixture_path, score_ijji
from ijji_truth import SCORE_BPM, SCORE_KEY


@pytest.mark.slow
def test_ijji_full_chart_matches_published_tab(tmp_path: Path):
    """자우림 「잊지」 전곡 탭: 타셋 후 버스 루트, 코러스 8분, 코다 온음표."""
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
    song = score_ijji(result.performed)
    assert song.sections["verse"].pitch_chroma >= 0.70
    assert song.sections["chorus"].pitch_chroma >= 0.65
    assert song.overall.pitch_chroma >= 0.65
    assert result.listen is not None
    assert result.listen.pitch_within_semitone >= 0.65
