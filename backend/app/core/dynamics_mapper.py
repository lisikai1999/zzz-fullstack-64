from dataclasses import dataclass, field

from app.core.music_model import (
    ChordElement,
    DynamicMark,
    Measure,
    MusicElement,
    NoteElement,
    RestElement,
    Voice,
)
from app.core.constants import DYNAMIC_VELOCITY, TICKS_PER_BEAT


def get_velocity_for_dynamic(mark: DynamicMark) -> int:
    return DYNAMIC_VELOCITY.get(mark.value, 80)


@dataclass
class DynamicsResult:
    measures: list[Measure]
    cc7_events: list[tuple[int, int]] = field(default_factory=list)


def _element_ticks(elem: MusicElement) -> int:
    fraction = elem.actual_duration
    quarter_notes = float(fraction) * 4
    return int(quarter_notes * TICKS_PER_BEAT)


def apply_dynamics_to_measures(measures: list[Measure]) -> DynamicsResult:
    """Walk measures, set velocity on notes, and collect CC#7 volume automation events."""
    current_velocity = 80
    cc7_events: list[tuple[int, int]] = []

    crescendo_active = False
    decrescendo_active = False
    ramp_start_velocity = current_velocity
    ramp_start_tick = 0
    ramp_elements: list[NoteElement | ChordElement] = []

    abs_tick = 0

    for measure in measures:
        for dyn in measure.dynamics:
            if dyn == DynamicMark.CRESCENDO:
                crescendo_active = True
                decrescendo_active = False
                ramp_start_velocity = current_velocity
                ramp_start_tick = abs_tick
                ramp_elements = []
            elif dyn == DynamicMark.DECRESCENDO:
                decrescendo_active = True
                crescendo_active = False
                ramp_start_velocity = current_velocity
                ramp_start_tick = abs_tick
                ramp_elements = []
            elif dyn in (DynamicMark.PP, DynamicMark.P, DynamicMark.MP, DynamicMark.MF, DynamicMark.F, DynamicMark.FF):
                target_velocity = get_velocity_for_dynamic(dyn)
                if crescendo_active or decrescendo_active:
                    _apply_ramp(ramp_elements, ramp_start_velocity, target_velocity)
                    curve = generate_cc7_curve(ramp_start_velocity, target_velocity, ramp_start_tick, abs_tick)
                    cc7_events.extend(curve)
                    crescendo_active = False
                    decrescendo_active = False
                    ramp_elements = []
                current_velocity = target_velocity

        for voice in measure.voices:
            voice_tick = abs_tick
            for elem in voice.elements:
                ticks = _element_ticks(elem)
                if isinstance(elem, (NoteElement, ChordElement)):
                    if elem.dynamic:
                        vel = get_velocity_for_dynamic(elem.dynamic)
                        if elem.dynamic == DynamicMark.CRESCENDO:
                            crescendo_active = True
                            decrescendo_active = False
                            ramp_start_velocity = current_velocity
                            ramp_start_tick = voice_tick
                            ramp_elements = []
                        elif elem.dynamic == DynamicMark.DECRESCENDO:
                            decrescendo_active = True
                            crescendo_active = False
                            ramp_start_velocity = current_velocity
                            ramp_start_tick = voice_tick
                            ramp_elements = []
                        else:
                            if crescendo_active or decrescendo_active:
                                _apply_ramp(ramp_elements, ramp_start_velocity, vel)
                                curve = generate_cc7_curve(ramp_start_velocity, vel, ramp_start_tick, voice_tick)
                                cc7_events.extend(curve)
                                crescendo_active = False
                                decrescendo_active = False
                                ramp_elements = []
                            current_velocity = vel

                    elem.velocity = current_velocity
                    if crescendo_active or decrescendo_active:
                        ramp_elements.append(elem)
                voice_tick += ticks

        measure_ticks = 0
        if measure.voices:
            max_voice_ticks = max(
                sum(_element_ticks(e) for e in v.elements)
                for v in measure.voices
            ) if measure.voices else 0
            measure_ticks = max_voice_ticks
        abs_tick += measure_ticks

    return DynamicsResult(measures=measures, cc7_events=cc7_events)


def _apply_ramp(elements: list[NoteElement | ChordElement], start_vel: int, end_vel: int) -> None:
    n = len(elements)
    if n == 0:
        return
    for i, elem in enumerate(elements):
        t = i / max(n - 1, 1)
        elem.velocity = int(start_vel + t * (end_vel - start_vel))


def generate_cc7_curve(
    start_velocity: int,
    end_velocity: int,
    start_tick: int,
    end_tick: int,
    resolution: int = 10,
) -> list[tuple[int, int]]:
    """Generate (absolute_tick, cc_value) pairs for a smooth volume ramp."""
    events = []
    if start_tick >= end_tick:
        return [(start_tick, end_velocity)]
    if resolution < 2:
        resolution = 2
    for i in range(resolution):
        t = i / (resolution - 1)
        tick = start_tick + int(t * (end_tick - start_tick))
        value = int(start_velocity + t * (end_velocity - start_velocity))
        value = max(0, min(127, value))
        events.append((tick, value))
    return events
