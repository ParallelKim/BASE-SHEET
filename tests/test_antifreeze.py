from pathlib import Path

import pytest

from base_sheet.pipeline import run
from antifreeze_eval import score_intro_midi
from antifreeze_truth import SCORE_BPM, SCORE_KEY, SECTIONS, played_hits
from song_score import score_song

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
    assert result.listen is not None
    assert result.listen.pitch_within_semitone >= 0.7
    assert result.midi_path.name.endswith(".mid")
    assert "quant" in result.quantized_midi_path.name


@pytest.mark.slow
def test_antifreeze_full_chart_matches_published_tab(tmp_path: Path):
    """전곡 탭: 인트로 8분 루트 + 전개/코러스 루트, 아웃트로 온음표."""
    if not FIXTURE.is_file():
        pytest.skip("fixture missing")
    result = run(
        FIXTURE,
        tmp_path,
        engine="crepe",
        bpm=SCORE_BPM,
        grid="8",
        key=SCORE_KEY,
        write_preview=False,
    )
    song = score_song(result.performed, played_hits(), SCORE_BPM, SECTIONS)
    assert song.sections["intro"].pitch_exact >= 0.90
    assert song.sections["intro"].pitch_chroma >= 0.95
    assert song.overall.pitch_chroma >= 0.70
    assert result.listen is not None
    assert result.listen.pitch_within_semitone >= 0.70
