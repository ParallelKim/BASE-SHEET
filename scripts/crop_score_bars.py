#!/usr/bin/env python3
"""Render published bass PDFs and crop every written bar.

Each crop is one measure with generous top/bottom padding so chord
symbols, lyrics, bass notation, TAB, and stems stay in frame.

    python scripts/crop_score_bars.py
    python scripts/crop_score_bars.py --ijji-pdf /path/to/있지.pdf

PDFs default to ``tests/fixtures/{ijji,Antifreeze}_bass_score.pdf``.
Writes ``tests/fixtures/score_crops/{ijji,antifreeze}/mNNN.png``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "score_crops"
SCALE = 3.5  # ~252 dpi

# Extra vertical room beyond the detected staves (pixels at SCALE).
# Chord symbols sit above the top staff; TAB stems hang well below.
PAD_TOP = 200
PAD_BOTTOM = 210
PAD_X = 24
NEIGHBOR_GAP = 16

IJJI_PDF_CANDIDATES = [
    ROOT / "tests" / "fixtures" / "ijji_bass_score.pdf",
    Path("/home/ubuntu/.cursor/projects/workspace/uploads/_B________1291.pdf"),
]
ANTIFREEZE_PDF = ROOT / "tests" / "fixtures" / "Antifreeze_bass_score.pdf"

# expected systems per 1-based page; bars are assigned 4 per system.
SONGS = {
    "ijji": {
        "n_bars": 72,
        "pages": [
            {"n_systems": 4},
            {"n_systems": 5},
            {"n_systems": 5},
            {"n_systems": 4},
        ],
    },
    "antifreeze": {
        "n_bars": 80,
        "pages": [
            {"n_systems": 4},
            {"n_systems": 4},
            {"n_systems": 3},
            {"n_systems": 4},
            {"n_systems": 5},
        ],
    },
}


def _staves(gray: np.ndarray) -> list[list[int]]:
    ink = (gray < 90).mean(axis=1)
    sm = np.convolve(ink, np.ones(5) / 5.0, mode="same")
    peaks, _ = find_peaks(sm, height=0.16, distance=10)
    groups: list[list[int]] = []
    for y in peaks:
        y = int(y)
        if not groups or y - groups[-1][-1] > 40:
            groups.append([y])
        else:
            groups[-1].append(y)
    return [g for g in groups if len(g) >= 4]


def _sizes_from_cuts(n: int, cut_after: set[int]) -> list[int]:
    sizes = []
    start = 0
    for i in range(n):
        if i in cut_after:
            sizes.append(i - start + 1)
            start = i + 1
    sizes.append(n - start)
    return [s for s in sizes if s > 0]


def _apply_cuts(staves: list[list[int]], cut_after: set[int]) -> list[list[list[int]]]:
    groups: list[list[list[int]]] = []
    cur: list[list[int]] = []
    for i, stave in enumerate(staves):
        cur.append(stave)
        if i in cut_after:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def _group_systems(staves: list[list[int]], n_systems: int) -> list[list[list[int]]]:
    n = len(staves)
    if n_systems < 1:
        raise ValueError("n_systems")
    if n == n_systems * 3:
        return [staves[i : i + 3] for i in range(0, n, 3)]
    starts = [g[0] for g in staves]
    gaps = sorted(
        ((starts[i + 1] - starts[i], i) for i in range(n - 1)),
        reverse=True,
    )
    cut_after: set[int] = set()
    for _gap, i in gaps:
        if len(cut_after) >= n_systems - 1:
            break
        trial = cut_after | {i}
        if min(_sizes_from_cuts(n, trial)) < 2:
            continue
        cut_after.add(i)
    for _gap, i in gaps:
        if len(cut_after) >= n_systems - 1:
            break
        cut_after.add(i)
    return _apply_cuts(staves, cut_after)


def _barlines(gray: np.ndarray, y0: int, y1: int, n_bars: int = 4) -> list[int]:
    h, w = gray.shape
    band = gray[max(0, y0) : min(h, y1), :]
    vin = (band < 80).mean(axis=0)
    peaks, _ = find_peaks(vin, height=0.22, distance=max(8, int(w * 0.10)))
    xs = [int(p) for p in peaks if 80 < p < w - 8]
    if len(xs) < n_bars + 1:
        peaks, _ = find_peaks(vin, height=0.12, distance=max(8, int(w * 0.08)))
        xs = [int(p) for p in peaks if 80 < p < w - 8]
    if len(xs) >= n_bars + 1:
        left, right = xs[0], xs[-1]
        targets = [left + i * (right - left) / n_bars for i in range(n_bars + 1)]
        chosen: list[int] = []
        used: set[int] = set()
        for t in targets:
            best = min((x for x in xs if x not in used), key=lambda x: abs(x - t))
            chosen.append(best)
            used.add(best)
        return sorted(chosen)
    left, right = 130, w - 80
    return [int(left + i * (right - left) / n_bars) for i in range(n_bars + 1)]


def _page_barlines(gray: np.ndarray, systems: list[list[list[int]]], n_bars: int = 4) -> list[int]:
    """Vote on 4-bar x-splits using every system on the page."""
    rows = []
    for sys_staves in systems:
        xs = _barlines(gray, sys_staves[0][0], sys_staves[-1][-1], n_bars=n_bars)
        if len(xs) == n_bars + 1:
            rows.append(xs)
    if not rows:
        h, w = gray.shape
        return _barlines(gray, 0, h, n_bars=n_bars)
    arr = np.array(rows, dtype=float)
    return [int(round(v)) for v in np.median(arr, axis=0)]


def _system_y(
    sys_staves: list[list[int]],
    prev_bottom: int | None,
    next_top: int | None,
    page_h: int,
) -> tuple[int, int]:
    """Pad far into the inter-system gap; never clip into a neighbor staff."""
    top = sys_staves[0][0]
    bot = sys_staves[-1][-1]
    y0 = top - PAD_TOP
    y1 = bot + PAD_BOTTOM
    if prev_bottom is not None:
        y0 = max(y0, prev_bottom + NEIGHBOR_GAP)
    if next_top is not None:
        y1 = min(y1, next_top - NEIGHBOR_GAP)
    return max(0, y0), min(page_h, y1)


def render_pdf(pdf_path: Path) -> list[Image.Image]:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    pages = []
    for page in pdf:
        pages.append(page.render(scale=SCALE).to_pil().convert("RGB"))
    return pages


def crop_song(name: str, pdf_path: Path, dest: Path) -> list[dict]:
    cfg = SONGS[name]
    pages = render_pdf(pdf_path)
    if len(pages) != len(cfg["pages"]):
        raise SystemExit(f"{name}: expected {len(cfg['pages'])} pages, got {len(pages)}")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "pages").mkdir(exist_ok=True)

    records: list[dict] = []
    bar = 1
    for pi, page_cfg in enumerate(cfg["pages"]):
        pil = pages[pi]
        pil.save(dest / "pages" / f"p{pi + 1}.png", optimize=True)
        gray = np.array(pil.convert("L"))
        staves = _staves(gray)
        n_sys = page_cfg["n_systems"]
        if len(staves) < n_sys:
            raise SystemExit(f"{name} p{pi + 1}: {len(staves)} staves < {n_sys} systems")
        systems = _group_systems(staves, n_sys)
        bottoms = [s[-1][-1] for s in systems]
        tops = [s[0][0] for s in systems]
        xs = _page_barlines(gray, systems, n_bars=4)
        for si, sys_staves in enumerate(systems):
            prev_b = bottoms[si - 1] if si else None
            next_t = tops[si + 1] if si + 1 < len(systems) else None
            y0, y1 = _system_y(sys_staves, prev_b, next_t, gray.shape[0])
            for bi in range(len(xs) - 1):
                x0 = max(0, xs[bi] - PAD_X)
                x1 = min(pil.width, xs[bi + 1] + PAD_X)
                crop = pil.crop((x0, y0, x1, y1))
                fname = f"m{bar:03d}.png"
                crop.save(dest / fname, optimize=True)
                records.append(
                    {
                        "song": name,
                        "bar": bar,
                        "page": pi + 1,
                        "system": si + 1,
                        "file": f"{name}/{fname}",
                        "box": [x0, y0, x1, y1],
                    }
                )
                bar += 1
    if bar - 1 != cfg["n_bars"]:
        raise SystemExit(f"{name}: cropped {bar - 1} bars, expected {cfg['n_bars']}")
    return records


def find_ijji_pdf(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit if explicit.is_file() else None
    for p in IJJI_PDF_CANDIDATES:
        if p.is_file():
            return p
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ijji-pdf", type=Path, default=None)
    parser.add_argument("--antifreeze-pdf", type=Path, default=ANTIFREEZE_PDF)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)

    all_records: list[dict] = []
    af_pdf = args.antifreeze_pdf
    if not af_pdf.is_file():
        print(f"missing Antifreeze PDF: {af_pdf}", file=sys.stderr)
        return 1
    print(f"antifreeze {af_pdf}")
    all_records.extend(crop_song("antifreeze", af_pdf, args.out / "antifreeze"))

    ij_pdf = find_ijji_pdf(args.ijji_pdf)
    if ij_pdf is None:
        print("skip ijji: PDF not found (pass --ijji-pdf)", file=sys.stderr)
    else:
        print(f"ijji {ij_pdf}")
        all_records.extend(crop_song("ijji", ij_pdf, args.out / "ijji"))

    manifest = args.out / "manifest.json"
    manifest.write_text(json.dumps(all_records, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(all_records)} bars -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
