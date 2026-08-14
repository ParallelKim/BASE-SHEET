"""Shared note types and bass MIDI range."""

from __future__ import annotations

from dataclasses import dataclass

# Standard 4-string bass sounding range (E1–G4).
BASS_MIDI_MIN = 28
BASS_MIDI_MAX = 67
UNVOICED = -1
MIN_NOTE_DURATION_S = 0.05  # CREPE Notes recommendation for bass
CREPE_PERIODICITY_FLOOR = 0.21
GM_ELECTRIC_BASS_FINGER = 33


@dataclass(frozen=True)
class NoteEvent:
    """Unquantized note from pitch tracking, times in seconds."""

    start: float
    end: float
    pitch: int
    amplitude: float = 0.8

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class QuantizedNote:
    """Note aligned to a metrical grid, times in quarter lengths."""

    offset_ql: float
    duration_ql: float
    pitch: int
    velocity: int = 80
