"""Antifreeze: one transcription, then per-section tests plus integration."""

from pathlib import Path

import pytest

from base_sheet.pipeline import run
from antifreeze_eval import score_intro_midi
from antifreeze_truth import SCORE_BPM, SCORE_KEY, SECTIONS, n_played_bars, played_hits
from song_score import score_song

FIXTURE = Path(__file__).parent / "fixtures" / "Antifreeze_bass_mixed.m4a"

# Pitch floors only on lock=score bars. late is skip/approx.
SECTION_FLOORS = {
    "intro": (0.90, 0.95),
    "verse": (0.90, 0.95),
    "middle_a": (0.45, 0.70),
    "middle_b": (0.45, 0.70),
    "vamp": (0.40, 0.65),
    "pedal": (0.40, 0.65),
    "chorus": (0.40, 0.65),
}

@pytest.fixture(scope="module")
def antifreeze_run(tmp_path_factory):
    if not FIXTURE.is_file():
        pytest.skip("fixture missing")
    out = tmp_path_factory.mktemp("antifreeze")
    result = run(
        FIXTURE,
        out,
        engine="crepe",
        bpm=SCORE_BPM,
        grid="8",
        key=SCORE_KEY,
        write_preview=False,
    )
    song = score_song(result.performed, played_hits(), SCORE_BPM, SECTIONS)
    return result, song


@pytest.mark.slow
def test_antifreeze_intro_eighth_density_and_clef(antifreeze_run):
    """분할: 인트로 8분음표 밀도 + 베이스 clef/조표."""
    result, _song = antifreeze_run
    xml = result.musicxml_path.read_text(encoding="utf-8")
    assert "<sign>F</sign>" in xml
    assert "<fifths>6</fifths>" in xml
    metrics = score_intro_midi(result.midi_path)
    assert metrics.pitch_acc >= 0.9
    assert metrics.mean_onsets_per_bar >= 5.5


@pytest.mark.slow
@pytest.mark.parametrize("section", list(SECTION_FLOORS))
def test_antifreeze_section_against_tab(antifreeze_run, section):
    """분할: 섹션별로 탭 피치를 채점해 약한 구간을 드러낸다."""
    _result, song = antifreeze_run
    assert section in song.sections, f"missing section {section}"
    sc = song.sections[section]
    exact_floor, chroma_floor = SECTION_FLOORS[section]
    assert sc.n_hits > 0, section
    assert sc.pitch_exact >= exact_floor, (
        f"{section} exact={sc.pitch_exact:.3f} chroma={sc.pitch_chroma:.3f} "
        f"missing={sc.missing}/{sc.n_hits}"
    )
    assert sc.pitch_chroma >= chroma_floor, (
        f"{section} exact={sc.pitch_exact:.3f} chroma={sc.pitch_chroma:.3f} "
        f"missing={sc.missing}/{sc.n_hits}"
    )


@pytest.mark.slow
def test_antifreeze_integration_all_sections(antifreeze_run):
    """통합: 분할 섹션이 한 타임라인으로 이어지고 전곡·청취 하한을 통과."""
    result, song = antifreeze_run
    assert set(song.sections) == set(SECTIONS)
    assert set(SECTION_FLOORS) | {"late"} == set(SECTIONS)
    n = n_played_bars()
    assert n == 99
    assert song.sections["late"].n_hits == 0
    assert song.overall.n_hits == sum(sc.n_hits for sc in song.sections.values())
    assert song.overall.pitch_chroma >= 0.70
    assert result.listen is not None
    assert result.listen.pitch_within_semitone >= 0.70
    assert song.sections["intro"].pitch_exact >= 0.90
    assert song.sections["verse"].pitch_exact >= 0.90
