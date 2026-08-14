"""Convert isolated (or leaky) bass audio into MIDI and MusicXML."""

from base_sheet.models import NoteEvent, QuantizedNote

__all__ = ["NoteEvent", "QuantizedNote", "run"]
__version__ = "0.1.0"


def __getattr__(name: str):
    if name == "run":
        from base_sheet.pipeline import run

        return run
    raise AttributeError(name)
