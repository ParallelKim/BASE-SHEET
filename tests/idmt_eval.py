"""Score BASE-SHEET against IDMT-SMT-Bass-Single-Track note annotations.

Dataset: https://doi.org/10.5281/zenodo.7544099 (CC BY-NC-ND 4.0).
Do not commit the wav/xml; fetch with ``python scripts/fetch_idmt_bass.py``.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from base_sheet.models import NoteEvent

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "idmt-smt-bass"
ONSET_TOL_S = 0.05


@dataclass
class TrackScore:
    track_id: str
    n_truth: int
    n_pred: int
    onset_f: float
    pitch_exact: float
    pitch_chroma: float
    pitch_within_semitone: float
    bpm: float


def dataset_ready(root: Path = FIXTURE_DIR) -> bool:
    return (root / "audio" / "001.wav").is_file() and (root / "annotation" / "001.xml").is_file()


def parse_annotation(xml_path: Path) -> list[NoteEvent]:
    tree = ET.parse(xml_path)
    notes: list[NoteEvent] = []
    for event in tree.getroot().findall("transcription/event"):
        pitch = int(event.findtext("pitch", default="-1"))
        start = float(event.findtext("onsetSec", default="0"))
        end = float(event.findtext("offsetSec", default="0"))
        if pitch < 0 or end <= start:
            continue
        notes.append(NoteEvent(start=start, end=end, pitch=pitch, amplitude=0.8))
    notes.sort(key=lambda n: n.start)
    return notes


def bpm_from_beats(csv_path: Path) -> float | None:
    if not csv_path.is_file():
        return None
    times: list[float] = []
    for line in csv_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        times.append(float(line.split(",")[0]))
    if len(times) < 4:
        return None
    diffs = [b - a for a, b in zip(times, times[1:]) if b > a]
    if not diffs:
        return None
    diffs.sort()
    median = diffs[len(diffs) // 2]
    bpm = 60.0 / median
    if bpm > 200:
        bpm /= 2.0
    if bpm < 50:
        bpm *= 2.0
    return float(bpm)


def match_onsets(
    truth: list[NoteEvent],
    pred: list[NoteEvent],
    *,
    onset_tol: float = ONSET_TOL_S,
) -> tuple[int, int, int, int]:
    """Return tp, exact-pitch hits, chroma hits, ±1-semitone hits."""
    used: set[int] = set()
    tp = exact = chroma = near = 0
    for tn in truth:
        best_i = None
        best_d = onset_tol + 1.0
        for i, pn in enumerate(pred):
            if i in used:
                continue
            d = abs(pn.start - tn.start)
            if d <= onset_tol and d < best_d:
                best_d = d
                best_i = i
        if best_i is None:
            continue
        used.add(best_i)
        pn = pred[best_i]
        tp += 1
        if pn.pitch == tn.pitch:
            exact += 1
        if pn.pitch % 12 == tn.pitch % 12:
            chroma += 1
        if abs(pn.pitch - tn.pitch) <= 1:
            near += 1
    return tp, exact, chroma, near


def f_measure(tp: int, n_pred: int, n_truth: int) -> float:
    if n_pred == 0 or n_truth == 0 or tp == 0:
        return 0.0
    prec = tp / n_pred
    rec = tp / n_truth
    return 2.0 * prec * rec / (prec + rec)


def score_track(track_id: str, root: Path = FIXTURE_DIR) -> TrackScore:
    from base_sheet.pipeline import run

    wav = root / "audio" / f"{track_id}.wav"
    xml = root / "annotation" / f"{track_id}.xml"
    beats = root / "misc" / "beats_csv" / f"{track_id}_beats.csv"
    truth = parse_annotation(xml)
    bpm = bpm_from_beats(beats)
    result = run(
        wav,
        root / "_out" / track_id,
        bpm=bpm,
        engine="crepe",
        grid="8",
        write_preview=False,
    )
    pred = result.performed
    tp, exact, chroma, near = match_onsets(truth, pred)
    n_t, n_p = len(truth), len(pred)
    return TrackScore(
        track_id=track_id,
        n_truth=n_t,
        n_pred=n_p,
        onset_f=f_measure(tp, n_p, n_t),
        pitch_exact=(exact / tp) if tp else 0.0,
        pitch_chroma=(chroma / tp) if tp else 0.0,
        pitch_within_semitone=(near / tp) if tp else 0.0,
        bpm=result.bpm,
    )


def iter_track_ids(root: Path = FIXTURE_DIR) -> list[str]:
    wavs = sorted((root / "audio").glob("*.wav"))
    return [p.stem for p in wavs]
