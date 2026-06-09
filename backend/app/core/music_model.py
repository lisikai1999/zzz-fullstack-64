from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Optional


class NoteDuration(str, Enum):
    WHOLE = "whole"
    HALF = "half"
    QUARTER = "quarter"
    EIGHTH = "eighth"
    SIXTEENTH = "sixteenth"


class Accidental(str, Enum):
    NONE = "none"
    SHARP = "sharp"
    FLAT = "flat"
    NATURAL = "natural"
    DOUBLE_SHARP = "double_sharp"
    DOUBLE_FLAT = "double_flat"


class DynamicMark(str, Enum):
    PP = "pp"
    P = "p"
    MP = "mp"
    MF = "mf"
    F = "f"
    FF = "ff"
    CRESCENDO = "crescendo"
    DECRESCENDO = "decrescendo"


class RepeatMark(str, Enum):
    DC = "dc"
    DS = "ds"
    CODA = "coda"
    SEGNO = "segno"
    FINE = "fine"
    VOLTA_1 = "volta_1"
    VOLTA_2 = "volta_2"
    REPEAT_START = "repeat_start"
    REPEAT_END = "repeat_end"


class Clef(str, Enum):
    TREBLE = "treble"
    BASS = "bass"
    ALTO = "alto"


class Articulation(str, Enum):
    TIE = "tie"
    SLUR_START = "slur_start"
    SLUR_END = "slur_end"
    STACCATO = "staccato"
    ACCENT = "accent"


DURATION_FRACTIONS: dict[NoteDuration, Fraction] = {
    NoteDuration.WHOLE: Fraction(1, 1),
    NoteDuration.HALF: Fraction(1, 2),
    NoteDuration.QUARTER: Fraction(1, 4),
    NoteDuration.EIGHTH: Fraction(1, 8),
    NoteDuration.SIXTEENTH: Fraction(1, 16),
}


@dataclass
class Pitch:
    step: str
    octave: int
    accidental: Accidental = Accidental.NONE

    @property
    def midi_number(self) -> int:
        step_semitones = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        accidental_offset = {
            Accidental.NONE: 0,
            Accidental.SHARP: 1,
            Accidental.FLAT: -1,
            Accidental.NATURAL: 0,
            Accidental.DOUBLE_SHARP: 2,
            Accidental.DOUBLE_FLAT: -2,
        }
        return (self.octave + 1) * 12 + step_semitones[self.step] + accidental_offset[self.accidental]


@dataclass
class TimeSignature:
    numerator: int = 4
    denominator: int = 4

    @property
    def measure_duration(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


@dataclass
class KeySignature:
    fifths: int = 0
    mode: str = "major"


@dataclass
class NoteElement:
    pitch: Pitch
    duration: NoteDuration
    dotted: bool = False
    articulations: list[Articulation] = field(default_factory=list)
    dynamic: Optional[DynamicMark] = None
    velocity: int = 80

    @property
    def actual_duration(self) -> Fraction:
        base = DURATION_FRACTIONS[self.duration]
        return base * Fraction(3, 2) if self.dotted else base


@dataclass
class RestElement:
    duration: NoteDuration
    dotted: bool = False

    @property
    def actual_duration(self) -> Fraction:
        base = DURATION_FRACTIONS[self.duration]
        return base * Fraction(3, 2) if self.dotted else base


@dataclass
class ChordElement:
    pitches: list[Pitch]
    duration: NoteDuration
    dotted: bool = False
    articulations: list[Articulation] = field(default_factory=list)
    dynamic: Optional[DynamicMark] = None
    velocity: int = 80

    @property
    def actual_duration(self) -> Fraction:
        base = DURATION_FRACTIONS[self.duration]
        return base * Fraction(3, 2) if self.dotted else base


MusicElement = NoteElement | RestElement | ChordElement


@dataclass
class Voice:
    voice_id: int
    elements: list[MusicElement] = field(default_factory=list)


@dataclass
class Measure:
    number: int
    voices: list[Voice] = field(default_factory=list)
    time_signature: Optional[TimeSignature] = None
    key_signature: Optional[KeySignature] = None
    tempo_bpm: Optional[int] = None
    repeat_marks: list[RepeatMark] = field(default_factory=list)
    dynamics: list[DynamicMark] = field(default_factory=list)
    volta: Optional[int] = None


@dataclass
class Staff:
    clef: Clef
    measures: list[Measure] = field(default_factory=list)
    instrument_name: str = "Piano"
    midi_program: int = 0


@dataclass
class Score:
    title: str
    composer: str = ""
    time_signature: TimeSignature = field(default_factory=TimeSignature)
    key_signature: KeySignature = field(default_factory=KeySignature)
    tempo_bpm: int = 120
    staves: list[Staff] = field(default_factory=list)
