"""Local web studio: fixture MIDI + score crops, and upload-to-transcribe jobs."""

from __future__ import annotations

import json
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(ROOT / "tests"))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "out"
LISTEN = OUT / "listen"
JOBS = OUT / "jobs"
CROPS = ROOT / "tests" / "fixtures" / "score_crops"
WEB_DATA = ROOT / "web" / "data"
MAX_UPLOAD_BYTES = 30 * 1024 * 1024
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aiff", ".aif", ".flac", ".ogg"}
STATIC_MIDI = {
    "ijji": ("ijji.mid", "ijji.quant.mid"),
    "antifreeze": ("antifreeze.mid", "antifreeze.quant.mid"),
}

_queue: list[str] = []
_q_lock = threading.Lock()
_worker_started = False


@dataclass
class Job:
    id: str
    status: str
    name: str
    bpm: float | None
    grid: str
    key: str | None
    error: str | None = None
    created: float = 0.0
    started: float | None = None
    finished: float | None = None

    def dir(self) -> Path:
        return JOBS / self.id

    def save(self) -> None:
        d = self.dir()
        d.mkdir(parents=True, exist_ok=True)
        (d / "job.json").write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")


def get_job(job_id: str) -> Job | None:
    return _load_job(job_id)


def _load_job(job_id: str) -> Job | None:
    path = JOBS / job_id / "job.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Job(**data)


def _play_ijji() -> list[int]:
    from ijji_chart import PLAY

    return list(PLAY)


def _play_af() -> list[int]:
    from antifreeze_chart import PLAY

    return list(PLAY)


def _first_midi(patterns: list[str]) -> Path | None:
    roots = [LISTEN, OUT]
    for folder in roots:
        if not folder.is_dir():
            continue
        for pat in patterns:
            hits = sorted(p for p in folder.glob(pat) if p.is_file() and ".quant." not in p.name)
            if hits:
                return hits[0]
    return None


def _quant_for(midi: Path | None) -> Path | None:
    if midi is None:
        return None
    q = midi.with_name(midi.stem + ".quant.mid")
    return q if q.is_file() else None


def _rel(path: Path | None) -> str | None:
    if path is None:
        return None
    resolved = path.resolve()
    try:
        return "/" + resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None


def _packaged_midi(song_id: str) -> Path | None:
    names = STATIC_MIDI.get(song_id)
    if not names:
        return None
    path = WEB_DATA / names[0]
    return path if path.is_file() else None


def _packaged_quant(song_id: str) -> Path | None:
    names = STATIC_MIDI.get(song_id)
    if not names:
        return None
    path = WEB_DATA / names[1]
    return path if path.is_file() else None


def _song_midi(song_id: str, patterns: list[str]) -> tuple[Path | None, Path | None]:
    midi = _first_midi(patterns) or _packaged_midi(song_id)
    quant = _quant_for(midi) or _packaged_quant(song_id)
    return midi, quant


def _audio_ijji() -> Path | None:
    from ijji_eval import fixture_path

    return fixture_path()


SECTION_LABELS = {
    "tacet": "타셋 (출판 쉼표)",
    "verse": "벌스",
    "chorus": "코러스",
    "inst": "간주",
    "drive": "드라이브",
    "coda_a": "코다 앞",
    "coda_b": "코다 뒤",
    "intro": "인트로",
    "middle_a": "미들 A",
    "middle_b": "미들 B",
    "vamp": "뱀프",
    "pedal": "페달",
    "late": "후반",
}

SECTION_HINTS = {
    "tacet": "출판 베이스가 쉬는 구간입니다. 피아노롤에 음이 있어도 킥·다른 저음 잔여일 수 있고, 탭 피치와 맞출 대상이 아닙니다. 「탭 있는 마디로」를 누르면 벌스부터 검수합니다.",
}

REVIEW = {
    "crop": "위 그림은 출판 그 마디입니다. 비어 있으면 베이스가 쉼표입니다.",
    "roll": "아래 칸은 스템에서 검출한 MIDI입니다. 믹스 잔여가 붙을 수 있습니다.",
    "listen": "스템처럼 들리는지는 헤드폰으로 비교(왼쪽=스템, 오른쪽=MIDI)를 듣습니다.",
    "score": "탭과 맞는지 보려면 쉼표가 아닌 마디에서 크롭 TAB과 피아노롤을 대조합니다.",
}


def fixture_songs() -> list[dict]:
    ijji_midi, ijji_quant = _song_midi("ijji", ["*있지*.mid", "*ijji*.mid"])
    af_midi, af_quant = _song_midi("antifreeze", ["*Antifreeze*.mid", "*antifreeze*.mid"])
    ijji_audio = _audio_ijji()
    af_audio = ROOT / "tests" / "fixtures" / "Antifreeze_bass_mixed.m4a"
    return [
        {
            "id": "ijji",
            "title": "있지 (자우림)",
            "kind": "fixture",
            "bpm": 84.0,
            "key": "F# minor",
            "grid": "8",
            "t0": 1.0714,
            "n_written": 72,
            "play": _play_ijji(),
            "sections": {
                "tacet": [0, 12],
                "verse": [12, 24],
                "chorus": [24, 32],
                "inst": [32, 44],
                "drive": [44, 60],
                "coda_a": [60, 64],
                "coda_b": [64, 72],
            },
            "midi": _rel(ijji_midi),
            "quant": _rel(ijji_quant),
            "audio": _rel(ijji_audio) if ijji_audio and ijji_audio.is_file() else None,
            "crop_song": "ijji",
            "n_crops": 72,
            "section_labels": SECTION_LABELS,
            "section_hints": SECTION_HINTS,
            "review": REVIEW,
            "review_from": 12,
        },
        {
            "id": "antifreeze",
            "title": "Antifreeze",
            "kind": "fixture",
            "bpm": 128.0,
            "key": "F#",
            "grid": "8",
            "t0": 0.7031,
            "n_written": 80,
            "play": _play_af(),
            "sections": {
                "intro": [0, 8],
                "verse": [8, 16],
                "middle_a": [16, 40],
                "middle_b": [40, 48],
                "vamp": [48, 74],
                "pedal": [74, 78],
                "chorus": [78, 102],
                "late": [102, 200],
            },
            "midi": _rel(af_midi),
            "quant": _rel(af_quant),
            "audio": _rel(af_audio) if af_audio.is_file() else None,
            "crop_song": "antifreeze",
            "n_crops": 80,
            "section_labels": SECTION_LABELS,
            "section_hints": SECTION_HINTS,
            "review": REVIEW,
            "review_from": 0,
        },
    ]


def job_song(job: Job) -> dict:
    d = job.dir()
    midis = sorted(d.glob("*.mid"))
    performed = next((p for p in midis if ".quant." not in p.name), None)
    preview = next(iter(sorted(d.glob("*.preview.wav"))), None)
    compare = next(iter(sorted(d.glob("*.compare.wav"))), None)
    done = job.status == "done"
    return {
        "id": f"job-{job.id}",
        "title": job.name,
        "kind": "job",
        "status": job.status,
        "error": job.error,
        "bpm": job.bpm,
        "key": job.key,
        "grid": job.grid,
        "t0": 0.0,
        "n_written": 0,
        "play": [],
        "sections": {},
        "midi": _rel(performed) if done else None,
        "quant": _rel(_quant_for(performed)) if done else None,
        "preview": _rel(preview) if done else None,
        "compare": _rel(compare) if done else None,
        "audio": None,
        "crop_song": None,
        "n_crops": 0,
        "job_id": job.id,
        "section_labels": {},
        "section_hints": {},
        "review": REVIEW,
        "review_from": 0,
    }


def list_jobs() -> list[Job]:
    if not JOBS.is_dir():
        return []
    out = []
    for path in sorted(JOBS.glob("*/job.json")):
        job = _load_job(path.parent.name)
        if job:
            out.append(job)
    return out


def catalog() -> dict:
    songs = fixture_songs()
    songs.extend(job_song(j) for j in list_jobs())
    return {"songs": songs, "upload_available": True, "static": False}


def static_catalog() -> dict:
    """Catalog for Firebase / Vercel: public MIDI + crop URLs, no upload jobs."""
    songs = []
    for song in fixture_songs():
        names = STATIC_MIDI.get(song["id"])
        if names:
            song = {
                **song,
                "midi": f"/data/{names[0]}",
                "quant": f"/data/{names[1]}",
                "audio": None,
            }
        else:
            song = {**song, "audio": None}
        n = int(song.get("n_crops") or 0)
        crop_song = song.get("crop_song")
        if crop_song and n:
            song["crops"] = [
                {"bar": i, "url": f"/score_crops/{crop_song}/m{i:03d}.png"}
                for i in range(1, n + 1)
            ]
        songs.append(song)
    return {"songs": songs, "upload_available": False, "static": True}


def crop_urls(song: str) -> list[dict]:
    if song not in {"ijji", "antifreeze"}:
        return []
    folder = CROPS / song
    items = []
    for p in sorted(folder.glob("m*.png")):
        try:
            bar = int(p.stem[1:])
        except ValueError:
            continue
        items.append({"bar": bar, "url": _rel(p)})
    return items


def written_bar(play: list[int], t: float, bpm: float, t0: float = 0.0) -> int | None:
    if bpm <= 0 or not play:
        return None
    bar_s = 240.0 / float(bpm)
    idx = int((max(0.0, t - t0)) / bar_s)
    if idx < 0 or idx >= len(play):
        return play[-1] if idx >= len(play) else play[0]
    return play[idx]


def create_job(
    filename: str,
    data: bytes,
    *,
    bpm: float | None,
    grid: str,
    key: str | None,
) -> Job:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("파일이 30MB를 넘습니다")
    suffix = Path(filename).suffix.lower()
    if suffix not in AUDIO_SUFFIXES:
        raise ValueError("wav / mp3 / m4a / flac / ogg / aiff 만 받습니다")
    if grid not in {"8", "16", "8t", "16t"}:
        raise ValueError("grid 는 8, 16, 8t, 16t")
    job = Job(
        id=uuid.uuid4().hex[:12],
        status="queued",
        name=Path(filename).name,
        bpm=bpm,
        grid=grid,
        key=key or None,
        created=time.time(),
    )
    job.dir().mkdir(parents=True, exist_ok=True)
    audio = job.dir() / f"input{suffix}"
    audio.write_bytes(data)
    job.save()
    with _q_lock:
        _queue.append(job.id)
    _ensure_worker()
    return job


def _ensure_worker() -> None:
    global _worker_started
    with _q_lock:
        if _worker_started:
            return
        _worker_started = True
    threading.Thread(target=_worker, name="studio-transcribe", daemon=True).start()


def _worker() -> None:
    while True:
        with _q_lock:
            job_id = _queue.pop(0) if _queue else None
        if job_id is None:
            time.sleep(0.4)
            continue
        job = _load_job(job_id)
        if job is None:
            continue
        job.status = "running"
        job.started = time.time()
        job.save()
        try:
            from base_sheet.pipeline import run

            audio = next(job.dir().glob("input.*"))
            run(
                audio,
                job.dir(),
                engine="crepe",
                bpm=job.bpm,
                grid=job.grid,
                key=job.key,
                write_preview=True,
            )
            job.status = "done"
        except Exception as exc:  # noqa: BLE001
            job.status = "error"
            job.error = str(exc)
        job.finished = time.time()
        job.save()


def job_public(job: Job) -> dict:
    return {**asdict(job), **job_song(job)}
