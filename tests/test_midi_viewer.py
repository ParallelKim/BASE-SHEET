from pathlib import Path

from base_sheet.studio import catalog, crop_urls, create_job, written_bar


def test_midi_viewer_page_exists():
    root = Path(__file__).resolve().parents[1]
    page = (root / "web" / "index.html").read_text(encoding="utf-8")
    assert "parseMidi" in (root / "web" / "studio.js").read_text(encoding="utf-8")
    assert 'id="roll"' in page
    assert 'id="score"' in page
    assert 'data-tab="upload"' in page
    assert (root / "web" / "studio.css").is_file()
    assert (root / "scripts" / "serve_midi_viewer.py").is_file()


def test_studio_catalog_lists_fixture_songs():
    data = catalog()
    ids = [s["id"] for s in data["songs"]]
    assert "ijji" in ids
    assert "antifreeze" in ids
    ijji = next(s for s in data["songs"] if s["id"] == "ijji")
    assert ijji["n_written"] == 72
    assert ijji["play"][0] == 1
    af = next(s for s in data["songs"] if s["id"] == "antifreeze")
    assert len(af["play"]) == 126
    assert af["play"][24] == 9


def test_studio_crops_cover_printed_bars():
    ijji = crop_urls("ijji")
    af = crop_urls("antifreeze")
    assert [c["bar"] for c in ijji] == list(range(1, 73))
    assert [c["bar"] for c in af] == list(range(1, 81))
    assert ijji[12]["url"].endswith("/m013.png")


def test_written_bar_follows_play_and_t0():
    play = list(range(1, 9)) + list(range(9, 25))
    assert written_bar(play, 0.0, 128.0, t0=0.0) == 1
    # one bar at 128 BPM is 1.875s
    assert written_bar(play, 1.9, 128.0, t0=0.0) == 2
    assert written_bar([1, 2, 3], 100.0, 84.0, t0=0.0) == 3


def test_create_job_rejects_bad_suffix():
    try:
        create_job("notes.txt", b"abc", bpm=84, grid="8", key=None)
    except ValueError as exc:
        assert "wav" in str(exc)
    else:
        raise AssertionError("expected ValueError")
