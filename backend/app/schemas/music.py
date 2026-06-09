from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class PitchSchema(BaseModel):
    step: str = Field(pattern=r"^[A-G]$")
    octave: int = Field(ge=0, le=9)
    accidental: str = "none"


class NoteElementSchema(BaseModel):
    type: Literal["note"] = "note"
    pitch: PitchSchema
    duration: str
    dotted: bool = False
    articulations: list[str] = Field(default_factory=list)
    dynamic: Optional[str] = None
    velocity: int = 80


class RestElementSchema(BaseModel):
    type: Literal["rest"] = "rest"
    duration: str
    dotted: bool = False


class ChordElementSchema(BaseModel):
    type: Literal["chord"] = "chord"
    pitches: list[PitchSchema]
    duration: str
    dotted: bool = False
    articulations: list[str] = Field(default_factory=list)
    dynamic: Optional[str] = None
    velocity: int = 80


MusicElementSchema = NoteElementSchema | RestElementSchema | ChordElementSchema


class VoiceSchema(BaseModel):
    voice_id: int = Field(ge=1, le=4)
    elements: list[NoteElementSchema | RestElementSchema | ChordElementSchema] = Field(default_factory=list)


class TimeSignatureSchema(BaseModel):
    numerator: int = 4
    denominator: int = 4


class KeySignatureSchema(BaseModel):
    fifths: int = Field(default=0, ge=-7, le=7)
    mode: str = "major"


class MeasureSchema(BaseModel):
    number: int
    voices: list[VoiceSchema] = Field(default_factory=list)
    time_signature: Optional[TimeSignatureSchema] = None
    key_signature: Optional[KeySignatureSchema] = None
    tempo_bpm: Optional[int] = None
    repeat_marks: list[str] = Field(default_factory=list)
    dynamics: list[str] = Field(default_factory=list)
    volta: Optional[int] = None


class StaffSchema(BaseModel):
    clef: str = "treble"
    measures: list[MeasureSchema] = Field(default_factory=list)
    instrument_name: str = "Piano"
    midi_program: int = 0


class ScoreContentSchema(BaseModel):
    title: str
    composer: str = ""
    time_signature: TimeSignatureSchema = Field(default_factory=TimeSignatureSchema)
    key_signature: KeySignatureSchema = Field(default_factory=KeySignatureSchema)
    tempo_bpm: int = 120
    staves: list[StaffSchema] = Field(default_factory=list)
