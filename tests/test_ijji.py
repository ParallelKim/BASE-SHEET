"""자우림 「있지」: one transcription, then per-section tests plus integration."""

import pytest

from base_sheet.pipeline import run
from ijji_eval import fixture_path, score_ijji
from ijji_truth import SCORE_BPM, SCORE_KEY, SECTIONS

# Pitch floors only on lock=score bars. Fills/coda_b are now print-locked.
SECTION_FLOORS = {
    "verse": (0.50, 0.70),
    "chorus": (0.40, 0.65),
    # Fills 37–39 are print-dense 16ths; chroma 0.55 until ornament onsets catch up.
    "inst": (0.35, 0.55),
    "drive": (0.35, 0.60),
    "coda_a": (0.30, 0.55),
    "coda_b": (0.25, 0.50),
}


@pytest.fixture(scope="module")
def ijji_run(tmp_path_factory):
    stem = fixture_path()
    if stem is None:
        pytest.skip("place tests/fixtures/ijji_bass.m4a or the uploaded stem")
    out = tmp_path_factory.mktemp("ijji")
    result = run(
        stem,
        out,
        engine="crepe",
        bpm=SCORE_BPM,
        grid="8",
        key=SCORE_KEY,
        write_preview=False,
    )
    song = score_ijji(result.performed)
    return result, song


@pytest.mark.slow
def test_ijji_tacet_has_no_tab_hits(ijji_run):
    """분할: 1–12마디는 악보상 쉼표."""
    _result, song = ijji_run
    assert song.sections["tacet"].n_hits == 0


@pytest.mark.slow
def test_ijji_coda_b_is_scored_from_print(ijji_run):
    """분할: 코다 후반(65–72)도 출판 탭 피치로 채점한다."""
    _result, song = ijji_run
    sc = song.sections["coda_b"]
    assert sc.n_hits > 0


@pytest.mark.slow
@pytest.mark.parametrize("section", list(SECTION_FLOORS))
def test_ijji_section_against_tab(ijji_run, section):
    """분할: 버스/코러스/간주/드라이브/코다를 따로 채점한다."""
    _result, song = ijji_run
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
def test_ijji_integration_all_sections(ijji_run):
    """통합: 타셋 이후 전 섹션이 한 곡으로 이어지고 청취 하한을 통과."""
    result, song = ijji_run
    assert set(song.sections) == set(SECTIONS)
    assert set(SECTION_FLOORS) | {"tacet"} == set(SECTIONS)
    assert song.overall.n_hits == sum(sc.n_hits for sc in song.sections.values())
    assert song.overall.pitch_chroma >= 0.65
    assert result.listen is not None
    assert result.listen.pitch_within_semitone >= 0.65
