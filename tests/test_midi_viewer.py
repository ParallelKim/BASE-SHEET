from pathlib import Path


def test_midi_viewer_page_exists():
    root = Path(__file__).resolve().parents[1]
    page = root / "web" / "index.html"
    text = page.read_text(encoding="utf-8")
    assert "parseMidi" in text
    assert 'id="roll"' in text
    assert (root / "scripts" / "serve_midi_viewer.py").is_file()
