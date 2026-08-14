from pathlib import Path

import pytest

from base_sheet.pipeline import run
from antifreeze_eval import score_intro_midi
from antifreeze_truth import SCORE_BPM, SCORE_KEY

FIXTURE = Path(__file__).parent / "fixtures" / "Antifreeze_bass_mixed.m4a"


@pytest.mark.slow
def test_antifreeze_intro_matches_tab_eighths(tmp_path: Path):
    """Compare against the published bass tab: 8 eighths/bar, q=128, F#."""
    if not FIXTURE.is_file():
        pytest.skip("fixture missing")
    result = run(
        FIXTURE,
        tmp_path,
        engine="crepe",
        bpm=SCORE_BPM,
        grid="8",
        key=SCORE_KEY,
    )
    xml = result.musicxml_path.read_text(encoding="utf-8")
    assert "<sign>F</sign>" in xml
    assert "<fifths>6</fifths>" in xml

    metrics = score_intro_midi(result.midi_path)
    assert metrics.pitch_acc >= 0.9
    assert metrics.mean_onsets_per_bar >= 5.5
    assert metrics.eighth_duration_frac >= 0.35
