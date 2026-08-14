"""CLI: python -m base_sheet bass.wav -o ./out [--bpm 96]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from base_sheet.models import MIN_NOTE_DURATION_S
from base_sheet.pipeline import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="base-sheet",
        description=(
            "Transcribe an isolated bass stem to MIDI and MusicXML. "
            "Bleed from imperfect source separation is tolerated; raise "
            "confidence via --min-duration if extra notes appear."
        ),
    )
    parser.add_argument("audio", type=Path, help="Path to bass audio (wav, mp3, m4a, …)")
    parser.add_argument("-o", "--output", type=Path, default=Path("out"))
    parser.add_argument(
        "--engine",
        default="crepe",
        choices=["crepe", "basic-pitch"],
        help="crepe = pYIN/torchcrepe + CREPE Notes split (default)",
    )
    parser.add_argument("--bpm", type=float, default=None, help="Skip tempo voting")
    parser.add_argument("--time-signature", default="4/4")
    parser.add_argument(
        "--grid",
        default="8",
        choices=["8", "16", "8t", "16t"],
        help="Quantization grid (8ths default; t = triplets)",
    )
    parser.add_argument("--key", default=None, help='e.g. "E minor" or "Em"')
    parser.add_argument(
        "--snap-key",
        action="store_true",
        help="Snap pitches to the key (given or estimated)",
    )
    parser.add_argument(
        "--min-duration",
        type=float,
        default=MIN_NOTE_DURATION_S,
        help="Drop notes shorter than this many seconds (default 0.05)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(
            args.audio,
            args.output,
            bpm=args.bpm,
            time_signature=args.time_signature,
            engine=args.engine,
            grid=args.grid,
            key=args.key,
            snap_key=args.snap_key,
            min_duration=args.min_duration,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Engine: {result.engine}")
    print(f"BPM: {result.bpm:.2f}")
    print(f"Time signature: {result.time_signature}")
    print(f"Key: {result.key}")
    print(f"Notes: {result.note_count}")
    print(f"Wrote (listen MIDI): {result.midi_path}")
    print(f"Wrote (quantized MIDI): {result.quantized_midi_path}")
    print(f"Wrote: {result.musicxml_path}")
    if result.listen is not None:
        print(
            f"Listen vs stem: pitch±1={result.listen.pitch_within_semitone:.1%} "
            f"chroma={result.listen.chroma_cosine:.2f} "
            f"(voiced frames {result.listen.voiced_frames})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
