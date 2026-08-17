#!/usr/bin/env python3
"""Transcribe the two fixture stems and list per-bar pitch vs the chart.

Writes compare.wav (L=stem R=MIDI) and a text report. Does not change charts.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from base_sheet.pipeline import run
from sheet_score import Hit, choose_t0, eighth_s, hit_time, pitch_at, score_hits
from song_score import score_song

PC = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _name(p: int | None) -> str:
    if p is None:
        return "—"
    return f"{PC[p % 12]}{p // 12 - 1}"


def _section_of(bar: int, sections: dict[str, tuple[int, int]]) -> str:
    for name, (a, b) in sections.items():
        if a <= bar < b:
            return name
    return "?"


def _report_song(
    name: str,
    result,
    hits: list[Hit],
    bpm: float,
    sections: dict,
    play: list[int],
    focus: list[str],
    out: Path,
) -> None:
    t0 = choose_t0(result.performed, hits, bpm)
    song = score_song(result.performed, hits, bpm, sections, t0=t0)
    lines = [
        f"# {name}",
        f"t0={t0:.4f}s bpm={bpm} notes={len(result.performed)}",
        f"compare={result.compare_path}",
        f"preview={result.preview_path}",
        f"midi={result.midi_path}",
        f"overall exact={song.overall.pitch_exact:.3f} chroma={song.overall.pitch_chroma:.3f} "
        f"missing={song.overall.missing}/{song.overall.n_hits}",
        "",
    ]
    for sec, sc in song.sections.items():
        if sc.n_hits == 0:
            continue
        lines.append(
            f"  {sec:10s} exact={sc.pitch_exact:.3f} chroma={sc.pitch_chroma:.3f} "
            f"missing={sc.missing}/{sc.n_hits}"
        )
    lines.append("")
    lines.append("played  writ  sec        hits  miss  exact  chroma  truth → pred")
    by_bar: dict[int, list[Hit]] = defaultdict(list)
    for h in hits:
        by_bar[h.bar].append(h)

    focus_set = set(focus) if focus else set(sections)
    for bar in sorted(by_bar):
        sec = _section_of(bar, sections)
        if sec not in focus_set:
            continue
        bar_hits = by_bar[bar]
        sc = score_hits(result.performed, bar_hits, bpm, t0)
        written = play[bar] if bar < len(play) else -1
        bits = []
        for h in bar_hits:
            t = hit_time(h, t0, bpm) + 0.35 * h.dur_eighths * eighth_s(bpm)
            pred = pitch_at(result.performed, t)
            mark = ""
            if pred is None:
                mark = " miss"
            elif pred != h.pitch:
                mark = " ≠" if pred % 12 == h.pitch % 12 else " ✗"
            bits.append(f"{_name(h.pitch)}→{_name(pred)}{mark}")
        lines.append(
            f"{bar:6d}  {written:4d}  {sec:10s} {sc.n_hits:4d}  {sc.missing:4d}  "
            f"{sc.pitch_exact:5.2f}  {sc.pitch_chroma:6.2f}  "
            + "  ".join(bits)
        )

    n_pred_bars = defaultdict(int)
    for n in result.performed:
        b = int((n.start - t0) / (8.0 * eighth_s(bpm)))
        n_pred_bars[b] += 1
    lines.append("")
    lines.append("onset density (pred notes whose start falls in the played bar):")
    for bar in sorted(by_bar):
        sec = _section_of(bar, sections)
        if sec not in focus_set:
            continue
        lines.append(
            f"  bar {bar:3d} {sec:10s} truth_hits={len(by_bar[bar]):2d} pred_onsets={n_pred_bars[bar]:2d}"
        )

    text = "\n".join(lines) + "\n"
    path = out / f"{name}_bars.txt"
    path.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {path}")
    _write_clips(name, result, t0, bpm, sections, out)


def _write_clips(name: str, result, t0: float, bpm: float, sections: dict, out: Path) -> None:
    if result.compare_path is None or not result.compare_path.is_file():
        return
    import soundfile as sf

    y, sr = sf.read(str(result.compare_path), always_2d=True)
    bar_s = 8.0 * eighth_s(bpm)
    for sec, (a, b) in sections.items():
        if sec in {"tacet"}:
            continue
        start = max(0, int((t0 + a * bar_s) * sr))
        end = min(len(y), int((t0 + b * bar_s) * sr))
        if end <= start:
            continue
        clip = out / f"{name}_{sec}.compare.wav"
        sf.write(str(clip), y[start:end], sr)
        print(f"clip {clip.name}  {a}–{b}  {(end - start) / sr:.1f}s")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "out" / "listen")
    parser.add_argument("--skip-ijji", action="store_true")
    parser.add_argument("--skip-antifreeze", action="store_true")
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)

    if not args.skip_ijji:
        from ijji_eval import fixture_path
        from ijji_truth import SCORE_BPM, SCORE_KEY, SECTIONS, played_hits

        stem = fixture_path()
        if stem is None:
            print("skip 있지: no stem")
        else:
            print(f"transcribe 있지 {stem}")
            result = run(
                stem,
                out,
                engine="crepe",
                bpm=SCORE_BPM,
                grid="8",
                key=SCORE_KEY,
                write_preview=True,
            )
            from ijji_chart import PLAY as IJ_PLAY

            _report_song(
                "ijji",
                result,
                played_hits(),
                SCORE_BPM,
                SECTIONS,
                IJ_PLAY,
                ["inst", "verse", "chorus", "drive", "coda_a", "coda_b"],
                out,
            )

    if not args.skip_antifreeze:
        from antifreeze_truth import SCORE_BPM, SCORE_KEY, SECTIONS, played_hits

        stem = ROOT / "tests" / "fixtures" / "Antifreeze_bass_mixed.m4a"
        print(f"transcribe Antifreeze {stem}")
        result = run(
            stem,
            out,
            engine="crepe",
            bpm=SCORE_BPM,
            grid="8",
            key=SCORE_KEY,
            write_preview=True,
        )
        from antifreeze_chart import PLAY as AF_PLAY

        _report_song(
            "antifreeze",
            result,
            played_hits(),
            SCORE_BPM,
            SECTIONS,
            AF_PLAY,
            ["intro", "verse", "middle_a", "middle_b", "vamp", "pedal", "chorus", "late"],
            out,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
