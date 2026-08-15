from pathlib import Path

import pytest

from idmt_eval import dataset_ready, parse_annotation, score_track, iter_track_ids
from base_sheet.models import NoteEvent

ROOT = Path(__file__).parent / "fixtures" / "idmt-smt-bass"


def test_parse_idmt_annotation_xml(tmp_path: Path):
    xml = tmp_path / "001.xml"
    xml.write_text(
        """<?xml version="1.0"?>
<instrumentRecording>
  <transcription>
    <event>
      <pitch>28</pitch>
      <onsetSec>0.1</onsetSec>
      <offsetSec>0.4</offsetSec>
    </event>
    <event>
      <pitch>33</pitch>
      <onsetSec>0.5</onsetSec>
      <offsetSec>0.9</offsetSec>
    </event>
  </transcription>
</instrumentRecording>
""",
        encoding="utf-8",
    )
    notes = parse_annotation(xml)
    assert notes == [
        NoteEvent(0.1, 0.4, 28, 0.8),
        NoteEvent(0.5, 0.9, 33, 0.8),
    ]


@pytest.mark.slow
def test_idmt_public_bass_lines_are_not_random():
    """IDMT-SMT-Bass-Single-Track (Abeßer et al.): 17 annotated DI bass lines."""
    if not dataset_ready(ROOT):
        pytest.skip("run: python scripts/fetch_idmt_bass.py")
    scores = [score_track(tid, ROOT) for tid in iter_track_ids(ROOT)]
    mean_f = sum(s.onset_f for s in scores) / len(scores)
    mean_chroma = sum(s.pitch_chroma for s in scores) / len(scores)
    mean_exact = sum(s.pitch_exact for s in scores) / len(scores)
    assert mean_f >= 0.72
    assert mean_chroma >= 0.90
    assert mean_exact >= 0.85
    assert all(s.n_pred > 0 for s in scores)

    by_id = {s.track_id: s for s in scores}
    # Clean fingered / muted lines should lock pitch.
    for tid in ("002", "003", "006", "010", "011", "015"):
        s = by_id[tid]
        assert s.onset_f >= 0.80, tid
        assert s.pitch_exact >= 0.94, tid
        assert s.pitch_chroma >= 0.95, tid
    # Slap / pop: f0 is noisy; require usable onsets, not invented pitch.
    for tid in ("007", "013", "016"):
        s = by_id[tid]
        assert s.onset_f >= 0.45, tid
        assert s.pitch_chroma >= 0.70, tid
    # Flageolet mix: keep chroma, do not fold harmonics to open strings.
    s017 = by_id["017"]
    assert s017.onset_f >= 0.45
    assert s017.pitch_chroma >= 0.75
    # Remaining fingerstyle / pick lines.
    for tid in ("001", "004", "005", "008", "009", "012", "014"):
        s = by_id[tid]
        assert s.onset_f >= 0.70, tid
        assert s.pitch_chroma >= 0.90, tid
