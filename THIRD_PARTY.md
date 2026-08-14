# Third-party algorithms

This repo does **not** vendor NeuralNote, BassLift, or YourMT3. The following
recipes are reimplemented in `src/base_sheet/` for personal, non-commercial
sheet-music use.

| Source | License | What we took |
|---|---|---|
| [CREPE Notes](https://github.com/xavriley/crepe_notes) (Riley & Dixon, SMC 2023) | research code; madmom has a non-commercial clause | inverted-confidence × \|Δf0\| boundaries; median pitch per segment; ≥50 ms notes; onset split for repeated pitches |
| [BassLift](https://github.com/winisza/BassLift) | MIT | median MIDI frames; ±12 jumps of 1–2 frames; multi-`start_bpm` voting; grids 8/16/8t/16t; merge same pitch after quantize |
| [Basic Pitch](https://github.com/spotify/basic-pitch) | Apache-2.0 | optional engine; frequency constraints; inferred onsets / Melodia trick stay in upstream; we drop pitch bends |
| [NeuralNote](https://github.com/DamRsn/NeuralNote) | Apache-2.0 | CLI knobs: sensitivity via min-duration, scale snap, user BPM — not the JUCE plugin |
| [instrument-agnostic-amt](https://github.com/anime-song/instrument-agnostic-amt) `bass_v2` | see upstream | treat over-segmentation as a bug; merge adjacent equal pitches |
| [torchcrepe](https://github.com/maxrmorrison/torchcrepe) | MIT | default f0 at 16 kHz / 10 ms; periodicity floor ~0.21; median on confidence; pYIN fallback with ≥4 periods of E1 |
| [music21](https://github.com/cuthbertLab/music21) | BSD-3 | bass clef, ties, key analysis; 16ths + triplets via `--grid` |
| [pretty_midi](https://github.com/craffel/pretty-midi) | MIT | GM electric bass program 33; `remove_invalid_notes`; no pitch-bend events |
| [librosa](https://github.com/librosa/librosa) | ISC | load, pYIN fallback, onset fallback, tempo |

madmom is optional and used only when installed. Personal non-commercial use is intended.
