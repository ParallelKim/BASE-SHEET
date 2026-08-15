#!/usr/bin/env python3
"""Local MIDI piano-roll + playback page.

    python scripts/serve_midi_viewer.py
    python scripts/serve_midi_viewer.py --dir ./out --port 8765
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "web" / "index.html"


class Handler(SimpleHTTPRequestHandler):
    midi_dir: Path = ROOT / "out"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print(f"  {self.address_string()}  {fmt % args}")

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/api/midis":
            items = []
            if self.midi_dir.is_dir():
                for p in sorted(self.midi_dir.glob("*.mid")):
                    rel = p.relative_to(ROOT).as_posix()
                    items.append({"name": p.name, "url": "/" + rel})
            body = json.dumps(items).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in ("/", "/web/", "/web/index.html"):
            self.path = "/web/index.html"
        super().do_GET()


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the BASE-SHEET MIDI viewer")
    parser.add_argument("--dir", type=Path, default=ROOT / "out", help="folder to list .mid from")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    Handler.midi_dir = args.dir.resolve()
    mimetypes.add_type("audio/midi", ".mid")
    mimetypes.add_type("audio/midi", ".midi")
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/web/index.html"
    print(f"MIDI viewer: {url}")
    print(f"Listing .mid in {Handler.midi_dir}")
    if not args.no_open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
