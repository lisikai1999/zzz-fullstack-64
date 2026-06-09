from fractions import Fraction
from app.core.music_model import NoteDuration, DURATION_FRACTIONS

STEP_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

PITCH_STEPS = ["C", "D", "E", "F", "G", "A", "B"]

KEY_SIGNATURE_MAP = {
    -7: ["Bb", "Eb", "Ab", "Db", "Gb", "Cb", "Fb"],
    -6: ["Bb", "Eb", "Ab", "Db", "Gb", "Cb"],
    -5: ["Bb", "Eb", "Ab", "Db", "Gb"],
    -4: ["Bb", "Eb", "Ab", "Db"],
    -3: ["Bb", "Eb", "Ab"],
    -2: ["Bb", "Eb"],
    -1: ["Bb"],
    0: [],
    1: ["F#"],
    2: ["F#", "C#"],
    3: ["F#", "C#", "G#"],
    4: ["F#", "C#", "G#", "D#"],
    5: ["F#", "C#", "G#", "D#", "A#"],
    6: ["F#", "C#", "G#", "D#", "A#", "E#"],
    7: ["F#", "C#", "G#", "D#", "A#", "E#", "B#"],
}

DYNAMIC_VELOCITY = {
    "pp": 30,
    "p": 50,
    "mp": 60,
    "mf": 70,
    "f": 90,
    "ff": 110,
}

GM_INSTRUMENTS = {
    0: "Acoustic Grand Piano",
    1: "Bright Acoustic Piano",
    4: "Electric Piano 1",
    24: "Acoustic Guitar (nylon)",
    25: "Acoustic Guitar (steel)",
    40: "Violin",
    41: "Viola",
    42: "Cello",
    56: "Trumpet",
    65: "Alto Sax",
    71: "Clarinet",
    73: "Flute",
}

AVAILABLE_DURATIONS = [
    NoteDuration.WHOLE,
    NoteDuration.HALF,
    NoteDuration.QUARTER,
    NoteDuration.EIGHTH,
    NoteDuration.SIXTEENTH,
]

TICKS_PER_BEAT = 480
