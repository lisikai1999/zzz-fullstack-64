import pytest
from fractions import Fraction

from app.core.music_model import (
    Accidental, ChordElement, Clef, DynamicMark, KeySignature,
    Measure, NoteDuration, NoteElement, Pitch, RepeatMark,
    RestElement, Score, Staff, TimeSignature, Voice,
)
from app.core.repeat_unfolder import unfold_repeats
from app.core.dynamics_mapper import apply_dynamics_to_measures, generate_cc7_curve
from app.services.validation import (
    auto_fill_rests, compute_voice_duration, validate_measure, validate_score, can_insert,
)
from app.services.midi_generator import generate_midi


def make_note(step="C", octave=4, duration=NoteDuration.QUARTER) -> NoteElement:
    return NoteElement(pitch=Pitch(step=step, octave=octave), duration=duration)


def make_rest(duration=NoteDuration.QUARTER) -> RestElement:
    return RestElement(duration=duration)


class TestValidation:
    def test_valid_measure(self):
        voice = Voice(voice_id=1, elements=[
            make_note("C", 4, NoteDuration.QUARTER),
            make_note("D", 4, NoteDuration.QUARTER),
            make_note("E", 4, NoteDuration.QUARTER),
            make_note("F", 4, NoteDuration.QUARTER),
        ])
        measure = Measure(number=1, voices=[voice])
        ts = TimeSignature(4, 4)
        errors = validate_measure(measure, ts)
        assert errors == []

    def test_invalid_measure_too_long(self):
        voice = Voice(voice_id=1, elements=[
            make_note("C", 4, NoteDuration.QUARTER),
            make_note("D", 4, NoteDuration.QUARTER),
            make_note("E", 4, NoteDuration.QUARTER),
            make_note("F", 4, NoteDuration.QUARTER),
            make_note("G", 4, NoteDuration.QUARTER),
        ])
        measure = Measure(number=1, voices=[voice])
        ts = TimeSignature(4, 4)
        errors = validate_measure(measure, ts)
        assert len(errors) == 1

    def test_auto_fill_rests(self):
        voice = Voice(voice_id=1, elements=[make_note("C", 4, NoteDuration.QUARTER)])
        ts = TimeSignature(4, 4)
        auto_fill_rests(voice, ts)
        total = compute_voice_duration(voice)
        assert total == Fraction(1, 1)

    def test_can_insert(self):
        voice = Voice(voice_id=1, elements=[
            make_note("C", 4, NoteDuration.QUARTER),
            make_note("D", 4, NoteDuration.QUARTER),
            make_note("E", 4, NoteDuration.QUARTER),
        ])
        ts = TimeSignature(4, 4)
        assert can_insert(voice, ts, make_note("F", 4, NoteDuration.QUARTER))
        assert not can_insert(voice, ts, make_note("F", 4, NoteDuration.HALF))

    def test_3_4_time(self):
        voice = Voice(voice_id=1, elements=[
            make_note("C", 4, NoteDuration.QUARTER),
            make_note("D", 4, NoteDuration.QUARTER),
            make_note("E", 4, NoteDuration.QUARTER),
        ])
        measure = Measure(number=1, voices=[voice])
        ts = TimeSignature(3, 4)
        errors = validate_measure(measure, ts)
        assert errors == []


class TestRepeatUnfolder:
    def test_simple_repeat(self):
        measures = [
            Measure(number=1, repeat_marks=[RepeatMark.REPEAT_START]),
            Measure(number=2),
            Measure(number=3, repeat_marks=[RepeatMark.REPEAT_END]),
            Measure(number=4),
        ]
        result = unfold_repeats(measures)
        nums = [m.number for m in result]
        assert nums == [1, 2, 3, 1, 2, 3, 4]

    def test_volta(self):
        measures = [
            Measure(number=1, repeat_marks=[RepeatMark.REPEAT_START]),
            Measure(number=2),
            Measure(number=3, volta=1, repeat_marks=[RepeatMark.REPEAT_END]),
            Measure(number=4, volta=2),
            Measure(number=5),
        ]
        result = unfold_repeats(measures)
        nums = [m.number for m in result]
        assert nums == [1, 2, 3, 1, 2, 4, 5]

    def test_dc_al_fine(self):
        measures = [
            Measure(number=1),
            Measure(number=2, repeat_marks=[RepeatMark.FINE]),
            Measure(number=3),
            Measure(number=4, repeat_marks=[RepeatMark.DC]),
        ]
        result = unfold_repeats(measures)
        nums = [m.number for m in result]
        assert nums == [1, 2, 3, 4, 1, 2]

    def test_ds_al_segno(self):
        measures = [
            Measure(number=1),
            Measure(number=2, repeat_marks=[RepeatMark.SEGNO]),
            Measure(number=3),
            Measure(number=4, repeat_marks=[RepeatMark.DS, RepeatMark.FINE]),
        ]
        result = unfold_repeats(measures)
        nums = [m.number for m in result]
        assert nums == [1, 2, 3, 4, 2, 3, 4]


class TestDynamicsMapper:
    def test_static_dynamics(self):
        note1 = make_note("C", 4, NoteDuration.QUARTER)
        note1.dynamic = DynamicMark.FF
        note2 = make_note("D", 4, NoteDuration.QUARTER)
        measures = [Measure(number=1, voices=[Voice(voice_id=1, elements=[note1, note2])])]
        result = apply_dynamics_to_measures(measures)
        assert result.measures[0].voices[0].elements[0].velocity == 110
        assert result.measures[0].voices[0].elements[1].velocity == 110

    def test_crescendo_generates_cc7(self):
        note1 = make_note("C", 4, NoteDuration.QUARTER)
        note1.dynamic = DynamicMark.P
        note2 = make_note("D", 4, NoteDuration.QUARTER)
        note2.dynamic = DynamicMark.CRESCENDO
        note3 = make_note("E", 4, NoteDuration.QUARTER)
        note4 = make_note("F", 4, NoteDuration.QUARTER)
        note4.dynamic = DynamicMark.FF
        measures = [Measure(number=1, voices=[Voice(voice_id=1, elements=[note1, note2, note3, note4])])]
        result = apply_dynamics_to_measures(measures)
        assert len(result.cc7_events) > 0
        assert result.cc7_events[0][1] == 50  # starts at p velocity
        assert result.cc7_events[-1][1] == 110  # ends at ff velocity

    def test_cc7_curve(self):
        curve = generate_cc7_curve(50, 100, 0, 480, resolution=5)
        assert len(curve) == 5
        assert curve[0] == (0, 50)
        assert curve[-1] == (480, 100)


class TestMidiGeneration:
    def test_generates_valid_midi(self):
        score = Score(
            title="Test",
            time_signature=TimeSignature(4, 4),
            tempo_bpm=120,
            staves=[Staff(
                clef=Clef.TREBLE,
                measures=[
                    Measure(number=1, voices=[Voice(voice_id=1, elements=[
                        make_note("C", 4, NoteDuration.QUARTER),
                        make_note("D", 4, NoteDuration.QUARTER),
                        make_note("E", 4, NoteDuration.QUARTER),
                        make_note("F", 4, NoteDuration.QUARTER),
                    ])]),
                ],
            )],
        )
        midi_bytes = generate_midi(score)
        assert midi_bytes[:4] == b'MThd'
        assert len(midi_bytes) > 50

    def test_midi_with_metronome(self):
        score = Score(
            title="Test",
            time_signature=TimeSignature(4, 4),
            tempo_bpm=120,
            staves=[Staff(
                clef=Clef.TREBLE,
                measures=[
                    Measure(number=1, voices=[Voice(voice_id=1, elements=[
                        make_note("C", 4, NoteDuration.WHOLE),
                    ])]),
                ],
            )],
        )
        midi_bytes = generate_midi(score, include_metronome=True)
        assert midi_bytes[:4] == b'MThd'

    def test_chord_midi(self):
        chord = ChordElement(
            pitches=[Pitch("C", 4), Pitch("E", 4), Pitch("G", 4)],
            duration=NoteDuration.WHOLE,
        )
        score = Score(
            title="Test",
            staves=[Staff(
                clef=Clef.TREBLE,
                measures=[Measure(number=1, voices=[Voice(voice_id=1, elements=[chord])])],
            )],
        )
        midi_bytes = generate_midi(score)
        assert midi_bytes[:4] == b'MThd'


class TestPitch:
    def test_midi_number(self):
        assert Pitch("C", 4).midi_number == 60
        assert Pitch("A", 4).midi_number == 69
        assert Pitch("C", 4, Accidental.SHARP).midi_number == 61
        assert Pitch("D", 4, Accidental.FLAT).midi_number == 61
