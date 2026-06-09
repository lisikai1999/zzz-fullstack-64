export type NoteDuration = 'whole' | 'half' | 'quarter' | 'eighth' | 'sixteenth'
export type Accidental = 'none' | 'sharp' | 'flat' | 'natural' | 'double_sharp' | 'double_flat'
export type DynamicMark = 'pp' | 'p' | 'mp' | 'mf' | 'f' | 'ff' | 'crescendo' | 'decrescendo'
export type RepeatMark = 'dc' | 'ds' | 'coda' | 'segno' | 'fine' | 'volta_1' | 'volta_2' | 'repeat_start' | 'repeat_end'
export type Clef = 'treble' | 'bass' | 'alto'
export type Articulation = 'tie' | 'slur_start' | 'slur_end' | 'staccato' | 'accent'

export interface Pitch {
  step: string
  octave: number
  accidental: Accidental
}

export interface TimeSignature {
  numerator: number
  denominator: number
}

export interface KeySignature {
  fifths: number
  mode: string
}

export interface NoteElement {
  type: 'note'
  pitch: Pitch
  duration: NoteDuration
  dotted: boolean
  articulations: Articulation[]
  dynamic: DynamicMark | null
  velocity: number
}

export interface RestElement {
  type: 'rest'
  duration: NoteDuration
  dotted: boolean
}

export interface ChordElement {
  type: 'chord'
  pitches: Pitch[]
  duration: NoteDuration
  dotted: boolean
  articulations: Articulation[]
  dynamic: DynamicMark | null
  velocity: number
}

export type MusicElement = NoteElement | RestElement | ChordElement

export interface Voice {
  voice_id: number
  elements: MusicElement[]
}

export interface Measure {
  number: number
  voices: Voice[]
  time_signature: TimeSignature | null
  key_signature: KeySignature | null
  tempo_bpm: number | null
  repeat_marks: RepeatMark[]
  dynamics: DynamicMark[]
  volta: number | null
}

export interface Staff {
  clef: Clef
  measures: Measure[]
  instrument_name: string
  midi_program: number
}

export interface ScoreContent {
  title: string
  composer: string
  time_signature: TimeSignature
  key_signature: KeySignature
  tempo_bpm: number
  staves: Staff[]
}

export interface ScoreListItem {
  id: number
  title: string
  composer: string
  created_at: string
  updated_at: string
}

export interface ScoreRead {
  id: number
  title: string
  composer: string
  created_at: string
  updated_at: string
  content: ScoreContent
}

export const DURATION_VALUES: Record<NoteDuration, number> = {
  whole: 1,
  half: 0.5,
  quarter: 0.25,
  eighth: 0.125,
  sixteenth: 0.0625,
}

export function pitchToMidi(pitch: Pitch): number {
  const stepSemitones: Record<string, number> = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }
  const accOffset: Record<Accidental, number> = {
    none: 0, sharp: 1, flat: -1, natural: 0, double_sharp: 2, double_flat: -2,
  }
  return (pitch.octave + 1) * 12 + stepSemitones[pitch.step] + accOffset[pitch.accidental]
}

export function midiToPitchName(midi: number): string {
  const names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
  const octave = Math.floor(midi / 12) - 1
  const note = names[midi % 12]
  return `${note}${octave}`
}
