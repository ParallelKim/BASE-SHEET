from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROPS = ROOT / "tests" / "fixtures" / "score_crops"


def test_crop_script_exists():
    assert (ROOT / "scripts" / "crop_score_bars.py").is_file()


def test_published_score_pdfs_are_in_fixtures():
    fixtures = ROOT / "tests" / "fixtures"
    assert (fixtures / "ijji_bass_score.pdf").is_file()
    assert (fixtures / "Antifreeze_bass_score.pdf").is_file()
    assert (fixtures / "ijji_bass_score.pdf").stat().st_size > 10_000
    assert (fixtures / "Antifreeze_bass_score.pdf").stat().st_size > 10_000


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
