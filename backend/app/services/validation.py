from fractions import Fraction

from app.core.music_model import (
    DURATION_FRACTIONS,
    Measure,
    MusicElement,
    NoteDuration,
    RestElement,
    Score,
    Staff,
    TimeSignature,
    Voice,
)


def get_effective_time_signature(measures: list[Measure], index: int) -> TimeSignature:
    for i in range(index, -1, -1):
        if measures[i].time_signature is not None:
            return measures[i].time_signature
    return TimeSignature(4, 4)


def compute_voice_duration(voice: Voice) -> Fraction:
    total = Fraction(0)
    for elem in voice.elements:
        total += elem.actual_duration
    return total


def validate_measure(measure: Measure, time_sig: TimeSignature) -> list[str]:
    errors = []
    expected = time_sig.measure_duration
    for voice in measure.voices:
        actual = compute_voice_duration(voice)
        if actual != expected:
            errors.append(
                f"Measure {measure.number}, Voice {voice.voice_id}: "
                f"duration {float(actual):.4f}, expected {float(expected):.4f}"
            )
    return errors


def validate_score(score: Score) -> dict[int, list[str]]:
    results: dict[int, list[str]] = {}
    for staff in score.staves:
        for idx, measure in enumerate(staff.measures):
            ts = get_effective_time_signature(staff.measures, idx)
            errs = validate_measure(measure, ts)
            if errs:
                results.setdefault(measure.number, []).extend(errs)
    return results


def auto_fill_rests(voice: Voice, time_sig: TimeSignature) -> None:
    """Fill remaining beats in a voice with appropriately sized rests."""
    current = compute_voice_duration(voice)
    remaining = time_sig.measure_duration - current
    if remaining <= 0:
        return

    ordered_durations = [
        NoteDuration.WHOLE,
        NoteDuration.HALF,
        NoteDuration.QUARTER,
        NoteDuration.EIGHTH,
        NoteDuration.SIXTEENTH,
    ]

    while remaining > 0:
        placed = False
        for dur in ordered_durations:
            frac = DURATION_FRACTIONS[dur]
            dotted_frac = frac * Fraction(3, 2)
            if dotted_frac <= remaining:
                voice.elements.append(RestElement(duration=dur, dotted=True))
                remaining -= dotted_frac
                placed = True
                break
            if frac <= remaining:
                voice.elements.append(RestElement(duration=dur, dotted=False))
                remaining -= frac
                placed = True
                break
        if not placed:
            break


def can_insert(voice: Voice, time_sig: TimeSignature, element: MusicElement) -> bool:
    """Check if inserting an element would exceed the measure duration."""
    current = compute_voice_duration(voice)
    return current + element.actual_duration <= time_sig.measure_duration
