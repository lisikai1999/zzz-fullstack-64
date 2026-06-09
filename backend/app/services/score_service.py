import json
from typing import Optional

from sqlalchemy.orm import Session

from app.core.music_model import (
    Accidental,
    Articulation,
    ChordElement,
    Clef,
    DynamicMark,
    KeySignature,
    Measure,
    NoteDuration,
    NoteElement,
    Pitch,
    RepeatMark,
    RestElement,
    Score,
    Staff,
    TimeSignature,
    Voice,
)
from app.models.score import ScoreRecord
from app.schemas.music import ScoreContentSchema
from app.schemas.score import ScoreCreate, ScoreUpdate


def schema_to_model(content: ScoreContentSchema) -> Score:
    staves = []
    for s in content.staves:
        measures = []
        for m in s.measures:
            voices = []
            for v in m.voices:
                elements = []
                for e in v.elements:
                    if e.type == "note":
                        elements.append(NoteElement(
                            pitch=Pitch(
                                step=e.pitch.step,
                                octave=e.pitch.octave,
                                accidental=Accidental(e.pitch.accidental),
                            ),
                            duration=NoteDuration(e.duration),
                            dotted=e.dotted,
                            articulations=[Articulation(a) for a in e.articulations],
                            dynamic=DynamicMark(e.dynamic) if e.dynamic else None,
                            velocity=e.velocity,
                        ))
                    elif e.type == "rest":
                        elements.append(RestElement(
                            duration=NoteDuration(e.duration),
                            dotted=e.dotted,
                        ))
                    elif e.type == "chord":
                        elements.append(ChordElement(
                            pitches=[
                                Pitch(step=p.step, octave=p.octave, accidental=Accidental(p.accidental))
                                for p in e.pitches
                            ],
                            duration=NoteDuration(e.duration),
                            dotted=e.dotted,
                            articulations=[Articulation(a) for a in e.articulations],
                            dynamic=DynamicMark(e.dynamic) if e.dynamic else None,
                            velocity=e.velocity,
                        ))
                voices.append(Voice(voice_id=v.voice_id, elements=elements))
            measures.append(Measure(
                number=m.number,
                voices=voices,
                time_signature=TimeSignature(m.time_signature.numerator, m.time_signature.denominator) if m.time_signature else None,
                key_signature=KeySignature(m.key_signature.fifths, m.key_signature.mode) if m.key_signature else None,
                tempo_bpm=m.tempo_bpm,
                repeat_marks=[RepeatMark(r) for r in m.repeat_marks],
                dynamics=[DynamicMark(d) for d in m.dynamics],
                volta=m.volta,
            ))
        staves.append(Staff(
            clef=Clef(s.clef),
            measures=measures,
            instrument_name=s.instrument_name,
            midi_program=s.midi_program,
        ))
    return Score(
        title=content.title,
        composer=content.composer,
        time_signature=TimeSignature(content.time_signature.numerator, content.time_signature.denominator),
        key_signature=KeySignature(content.key_signature.fifths, content.key_signature.mode),
        tempo_bpm=content.tempo_bpm,
        staves=staves,
    )


def list_scores(db: Session, skip: int = 0, limit: int = 50) -> list[ScoreRecord]:
    return db.query(ScoreRecord).order_by(ScoreRecord.updated_at.desc()).offset(skip).limit(limit).all()


def get_score(db: Session, score_id: int) -> Optional[ScoreRecord]:
    return db.query(ScoreRecord).filter(ScoreRecord.id == score_id).first()


def create_score(db: Session, data: ScoreCreate) -> ScoreRecord:
    record = ScoreRecord(
        title=data.title,
        composer=data.composer,
        content_json=data.content.model_dump_json(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_score(db: Session, score_id: int, data: ScoreUpdate) -> Optional[ScoreRecord]:
    record = db.query(ScoreRecord).filter(ScoreRecord.id == score_id).first()
    if not record:
        return None
    if data.title is not None:
        record.title = data.title
    if data.composer is not None:
        record.composer = data.composer
    if data.content is not None:
        record.content_json = data.content.model_dump_json()
    db.commit()
    db.refresh(record)
    return record


def delete_score(db: Session, score_id: int) -> bool:
    record = db.query(ScoreRecord).filter(ScoreRecord.id == score_id).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True
