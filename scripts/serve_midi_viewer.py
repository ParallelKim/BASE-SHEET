#!/usr/bin/env python3
"""BASE-SHEET studio: piano roll, score crops, and stem upload.

    python scripts/serve_midi_viewer.py
    python scripts/serve_midi_viewer.py --host 0.0.0.0 --port 8765
"""

from __future__ import annotations

import argparse
import cgi
import json
import mimetypes
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from base_sheet.studio import (  # noqa: E402
    MAX_UPLOAD_BYTES,
    catalog,
    create_job,
    crop_urls,
    get_job,
    job_public,
    list_jobs,
)

mimetypes.add_type("audio/midi", ".mid")
mimetypes.add_type("audio/midi", ".midi")
mimetypes.add_type("audio/mp4", ".m4a")


def _json(handler: SimpleHTTPRequestHandler, payload, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print(f"  {self.address_string()}  {fmt % args}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            _json(self, {"ok": True})
            return
        if path == "/api/catalog":
            _json(self, catalog())
            return
        if path == "/api/jobs":
            _json(self, {"jobs": [job_public(j) for j in list_jobs()]})
            return
        if path.startswith("/api/jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            job = get_job(job_id)
            if job is None:
                _json(self, {"error": "없는 작업"}, 404)
                return
            _json(self, job_public(job))
            return
        if path.startswith("/api/crops/"):
            song = path.rsplit("/", 1)[-1]
            _json(self, {"crops": crop_urls(song)})
            return
        if path in ("/", "/index.html", "/web/", "/web/index.html"):
            self.path = "/web/index.html"
        elif path in ("/studio.js", "/studio.css"):
            self.path = "/web" + path
        elif path.startswith("/data/"):
            self.path = "/web" + path
        elif path.startswith("/score_crops/"):
            self.path = "/tests/fixtures" + path
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/jobs":
            _json(self, {"error": "없는 주소"}, 404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_UPLOAD_BYTES + 4096:
            _json(self, {"error": "파일이 너무 큽니다"}, 413)
            return
        ctype, pdict = cgi.parse_header(self.headers.get("Content-Type", ""))
        if ctype != "multipart/form-data" or "boundary" not in pdict:
            _json(self, {"error": "multipart/form-data 가 필요합니다"}, 400)
            return
        pdict["boundary"] = pdict["boundary"].encode("ascii")
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")},
            keep_blank_values=True,
        )
        upload = form["audio"] if "audio" in form else None
        if upload is None or not getattr(upload, "file", None):
            _json(self, {"error": "audio 파일이 없습니다"}, 400)
            return
        data = upload.file.read(MAX_UPLOAD_BYTES + 1)
        filename = Path(getattr(upload, "filename", None) or "stem.wav").name
        bpm_raw = form.getfirst("bpm") or ""
        key = (form.getfirst("key") or "").strip() or None
        grid = (form.getfirst("grid") or "8").strip()
        try:
            bpm = float(bpm_raw) if bpm_raw.strip() else None
        except ValueError:
            _json(self, {"error": "BPM 숫자를 확인하세요"}, 400)
            return
        try:
            job = create_job(filename, data, bpm=bpm, grid=grid, key=key)
        except ValueError as exc:
            _json(self, {"error": str(exc)}, 400)
            return
        _json(self, job_public(job), 202)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the BASE-SHEET studio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"BASE-SHEET studio: {url}")
    print(f"bind {args.host}:{args.port}")
    if not args.no_open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
