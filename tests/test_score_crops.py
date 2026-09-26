from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROPS = ROOT / "tests" / "fixtures" / "score_crops"


def test_crop_script_exists():
    assert (ROOT / "scripts" / "crop_score_bars.py").is_file()


def test_published_score_pdfs_are_in_fixtures():
    fixtures = ROOT / "tests" / "fixtures"
    for name in (
        "ijji_bass_score.pdf",
        "Antifreeze_bass_score.pdf",
        "도시의 밤_bass_score.pdf",
        "나이_bass_score.pdf",
        "Wake Me Up When September Ends_bass_score.pdf",
        "삐딱하게_bass_score.pdf",
        "박하사탕_bass_score.pdf",
    ):
        path = fixtures / name
        assert path.is_file(), name
        assert path.stat().st_size > 10_000, name


def test_mixed_stems_are_in_fixtures():
    fixtures = ROOT / "tests" / "fixtures"
    stems = (
        "Antifreeze_bass_mixed.m4a",
        "있지 - 자우림_bass_mixed.m4a",
        "도시의 밤 - 소울라이츠_bass_mixed.mp3",
        "나이 - 윤종신_bass_mixed.mp3",
        "Wake Me Up When September Ends - Green Day_bass_mixed.mp3",
        "삐딱하게 - G-DRAGON_bass_mixed.mp3",
        "박하사탕 - YB_bass_mixed.mp3",
    )
    for name in stems:
        path = fixtures / name
        assert path.is_file() and path.stat().st_size > 100_000, name


def test_ijji_bar_crops_cover_72_measures():
    bars = sorted((CROPS / "ijji").glob("m*.png"))
    assert [p.name for p in bars] == [f"m{i:03d}.png" for i in range(1, 73)]
    for p in bars:
        assert p.stat().st_size > 2_000, p


def test_antifreeze_bar_crops_cover_80_measures():
    bars = sorted((CROPS / "antifreeze").glob("m*.png"))
    assert [p.name for p in bars] == [f"m{i:03d}.png" for i in range(1, 81)]
    for p in bars:
        assert p.stat().st_size > 2_000, p


def test_score_crop_pages_and_manifest_exist():
    assert (CROPS / "ijji" / "pages" / "p1.png").is_file()
    assert (CROPS / "ijji" / "pages" / "p4.png").is_file()
    assert (CROPS / "antifreeze" / "pages" / "p5.png").is_file()
    text = (CROPS / "manifest.json").read_text(encoding="utf-8")
    assert '"bar": 72' in text
    assert '"bar": 80' in text
    assert '"song": "ijji"' in text
    assert '"song": "antifreeze"' in text
