import io
from copy import deepcopy

import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage

from app.core.constants import TICKS_PER_BEAT
from app.core.dynamics_mapper import apply_dynamics_to_measures, DynamicsResult
from app.core.music_model import (
    ChordElement,
    Measure,
    NoteElement,
    RestElement,
    Score,
    Staff,
    TimeSignature,
    Voice,
)
from app.core.repeat_unfolder import unfold_repeats
from app.services.validation import get_effective_time_signature


def duration_to_ticks(element) -> int:
    fraction = element.actual_duration
    quarter_notes = float(fraction) * 4
    return int(quarter_notes * TICKS_PER_BEAT)


def merge_voices_to_events(
    voices: list[Voice],
    channel: int,
    cc7_events: list[tuple[int, int]] | None = None,
    measure_start_tick: int = 0,
) -> list[Message]:
    """Merge multiple voices + CC#7 events into a single sorted event list with delta times."""
    all_events: list[tuple[int, Message]] = []

    for voice in voices:
        abs_tick = measure_start_tick
        for elem in voice.elements:
            ticks = duration_to_ticks(elem)
            if isinstance(elem, NoteElement):
                all_events.append((abs_tick, Message(
                    "note_on", note=elem.pitch.midi_number,
                    velocity=elem.velocity, channel=channel,
                )))
                all_events.append((abs_tick + ticks, Message(
                    "note_off", note=elem.pitch.midi_number,
                    velocity=0, channel=channel,
                )))
            elif isinstance(elem, ChordElement):
                for pitch in elem.pitches:
                    all_events.append((abs_tick, Message(
                        "note_on", note=pitch.midi_number,
                        velocity=elem.velocity, channel=channel,
                    )))
                    all_events.append((abs_tick + ticks, Message(
                        "note_off", note=pitch.midi_number,
                        velocity=0, channel=channel,
                    )))
            abs_tick += ticks

    if cc7_events:
        for tick, value in cc7_events:
            all_events.append((tick, Message(
                "control_change", control=7, value=value, channel=channel,
            )))

    all_events.sort(key=lambda e: (e[0], 0 if e[1].type == "control_change" else 1 if e[1].type == "note_on" else 2))

    messages: list[Message] = []
    prev_tick = 0
    for abs_tick, msg in all_events:
        delta = abs_tick - prev_tick
        messages.append(msg.copy(time=delta))
        prev_tick = abs_tick

    return messages


def generate_metronome_track(
    measures: list[Measure], default_ts: TimeSignature
) -> MidiTrack:
    track = MidiTrack()
    hi_note = 76
    lo_note = 77

    for idx, measure in enumerate(measures):
        ts = measure.time_signature or default_ts
        beats = ts.numerator
        beat_ticks = int((4 / ts.denominator) * TICKS_PER_BEAT)

        for beat in range(beats):
            note = hi_note if beat == 0 else lo_note
            velocity = 100 if beat == 0 else 70
            track.append(Message("note_on", note=note, velocity=velocity, channel=9, time=0))
            track.append(Message("note_off", note=note, velocity=0, channel=9, time=beat_ticks))

    return track


def generate_midi(
    score: Score,
    include_metronome: bool = False,
    start_measure: int = 1,
    end_measure: int | None = None,
) -> bytes:
    mid = MidiFile(type=1, ticks_per_beat=TICKS_PER_BEAT)

    tempo_track = MidiTrack()
    mid.tracks.append(tempo_track)
    tempo_track.append(MetaMessage("set_tempo", tempo=mido.bpm2tempo(score.tempo_bpm), time=0))
    tempo_track.append(MetaMessage(
        "time_signature",
        numerator=score.time_signature.numerator,
        denominator=score.time_signature.denominator,
        time=0,
    ))
    tempo_track.append(MetaMessage("end_of_track", time=0))

    for staff_idx, staff in enumerate(score.staves):
        channel = staff_idx if staff_idx < 9 else staff_idx + 1

        performance_measures = unfold_repeats(deepcopy(staff.measures))

        if end_measure is not None:
            performance_measures = [m for m in performance_measures if start_measure <= m.number <= end_measure]
        elif start_measure > 1:
            performance_measures = [m for m in performance_measures if m.number >= start_measure]

        dynamics_result: DynamicsResult = apply_dynamics_to_measures(performance_measures)
        performance_measures = dynamics_result.measures
        cc7_events = dynamics_result.cc7_events

        track = MidiTrack()
        mid.tracks.append(track)
        track.append(MetaMessage("track_name", name=staff.instrument_name, time=0))
        track.append(Message("program_change", program=staff.midi_program, channel=channel, time=0))

        msgs = merge_voices_to_events(
            _flatten_measure_voices(performance_measures),
            channel,
            cc7_events=cc7_events,
            measure_start_tick=0,
        )
        track.extend(msgs)

        track.append(MetaMessage("end_of_track", time=0))

    if include_metronome and score.staves:
        all_perf_measures = unfold_repeats(deepcopy(score.staves[0].measures))
        if end_measure is not None:
            all_perf_measures = [m for m in all_perf_measures if start_measure <= m.number <= end_measure]
        elif start_measure > 1:
            all_perf_measures = [m for m in all_perf_measures if m.number >= start_measure]

        metro_track = generate_metronome_track(all_perf_measures, score.time_signature)
        metro_track.append(MetaMessage("end_of_track", time=0))
        mid.tracks.append(metro_track)

    buffer = io.BytesIO()
    mid.save(file=buffer)
    buffer.seek(0)
    return buffer.read()


def _flatten_measure_voices(measures: list[Measure]) -> list[Voice]:
    """Flatten all measures into virtual voices with correct absolute timing.

    Each voice's elements are concatenated across measures in order.
    Different voice_ids become separate entries.
    """
    voice_map: dict[int, list] = {}
    for measure in measures:
        all_voice_ids = set(v.voice_id for v in measure.voices) if measure.voices else {1}
        for voice in measure.voices:
            if voice.voice_id not in voice_map:
                voice_map[voice.voice_id] = []
            voice_map[voice.voice_id].extend(voice.elements)

    return [Voice(voice_id=vid, elements=elems) for vid, elems in voice_map.items()]
