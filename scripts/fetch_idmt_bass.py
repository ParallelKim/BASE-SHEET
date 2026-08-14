"""Download the IDMT-SMT-Bass-Single-Track public bass A2M eval set."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

ZENODO_URL = (
    "https://zenodo.org/api/records/7544099/files/"
    "IDMT-SMT-BASS-SINGLE-TRACKS.zip/content"
)
ZIP_MD5 = "c85540c664e8b13badd86880bacf11fa"
DEFAULT_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "idmt-smt-bass"


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(dest: Path = DEFAULT_DIR, *, force: bool = False) -> Path:
    dest = Path(dest)
    marker = dest / "audio" / "001.wav"
    if marker.is_file() and not force:
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "IDMT-SMT-BASS-SINGLE-TRACKS.zip"
    print(f"Downloading IDMT-SMT-Bass-Single-Track → {zip_path}")
    urlretrieve(ZENODO_URL, zip_path)
    digest = _md5(zip_path)
    if digest != ZIP_MD5:
        raise RuntimeError(f"checksum mismatch: {digest} != {ZIP_MD5}")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    zip_path.unlink(missing_ok=True)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    path = fetch(args.output, force=args.force)
    print(f"Ready: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
