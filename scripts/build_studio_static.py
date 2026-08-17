#!/usr/bin/env python3
"""Copy fixture MIDI and score crops into web/ for static hosting.

    python3 scripts/build_studio_static.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from base_sheet.studio import STATIC_MIDI, static_catalog  # noqa: E402
from base_sheet.studio import LISTEN, OUT  # noqa: E402

WEB = ROOT / "web"
DATA = WEB / "data"
CROPS_SRC = ROOT / "tests" / "fixtures" / "score_crops"
CROPS_DST = WEB / "score_crops"


def _first_midi(patterns: list[str], *, quant: bool) -> Path | None:
    for folder in (LISTEN, OUT, DATA):
        if not folder.is_dir():
            continue
        for pat in patterns:
            hits = sorted(
                p
                for p in folder.glob(pat)
                if p.is_file() and ((".quant." in p.name) == quant)
            )
            if hits:
                return hits[0]
    return None


def _copy_midi(dest_name: str, patterns: list[str], *, quant: bool) -> Path | None:
    dest = DATA / dest_name
    src = _first_midi(patterns, quant=quant)
    if src is None:
        if dest.is_file():
            return dest
        print(f"warning: no MIDI for {dest_name} (looked for {patterns})", file=sys.stderr)
        return None
    if src.resolve() == dest.resolve():
        return dest
    DATA.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"copied {src.relative_to(ROOT)} -> web/data/{dest_name}")
    return dest


def _copy_crops() -> None:
    if not CROPS_SRC.is_dir():
        raise SystemExit(f"missing {CROPS_SRC}")
    if CROPS_DST.is_symlink() or CROPS_DST.is_file():
        CROPS_DST.unlink()
    elif CROPS_DST.is_dir():
        shutil.rmtree(CROPS_DST)
    shutil.copytree(CROPS_SRC, CROPS_DST)
    n = sum(1 for _ in CROPS_DST.rglob("m*.png"))
    print(f"copied score crops ({n} png) -> web/score_crops/")


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    _copy_midi("ijji.mid", ["*있지*.mid", "*ijji*.mid"], quant=False)
    _copy_midi("ijji.quant.mid", ["*있지*.quant.mid", "*ijji*.quant.mid"], quant=True)
    _copy_midi("antifreeze.mid", ["*Antifreeze*.mid", "*antifreeze*.mid"], quant=False)
    _copy_midi(
        "antifreeze.quant.mid",
        ["*Antifreeze*.quant.mid", "*antifreeze*.quant.mid"],
        quant=True,
    )
    _copy_crops()
    catalog = static_catalog()
    for song in catalog["songs"]:
        names = STATIC_MIDI.get(song["id"])
        if not names:
            continue
        if not (DATA / names[0]).is_file():
            song["midi"] = None
        if not (DATA / names[1]).is_file():
            song["quant"] = None
    (DATA / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("wrote web/data/catalog.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
