import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ScoreContent, Staff, Measure, Voice, MusicElement,
  NoteElement, RestElement, ChordElement,
  NoteDuration, TimeSignature, Pitch, Accidental,
} from '@/types/music'
import { DURATION_VALUES } from '@/types/music'

function defaultScore(): ScoreContent {
  const voice: Voice = {
    voice_id: 1,
    elements: [{ type: 'rest', duration: 'whole', dotted: false }],
  }
  const measures: Measure[] = Array.from({ length: 4 }, (_, i) => ({
    number: i + 1,
    voices: [{ voice_id: 1, elements: [{ type: 'rest', duration: 'whole', dotted: false }] }],
    time_signature: i === 0 ? { numerator: 4, denominator: 4 } : null,
    key_signature: i === 0 ? { fifths: 0, mode: 'major' } : null,
    tempo_bpm: null,
    repeat_marks: [],
    dynamics: [],
    volta: null,
  }))
  return {
    title: '新乐谱',
    composer: '',
    time_signature: { numerator: 4, denominator: 4 },
    key_signature: { fifths: 0, mode: 'major' },
    tempo_bpm: 120,
    staves: [{
      clef: 'treble',
      measures,
      instrument_name: 'Piano',
      midi_program: 0,
    }],
  }
}

function getActualDuration(elem: MusicElement): number {
  const base = DURATION_VALUES[elem.duration]
  return elem.dotted ? base * 1.5 : base
}

function getMeasureDuration(ts: TimeSignature): number {
  return ts.numerator / ts.denominator
}

function computeVoiceDuration(voice: Voice): number {
  return voice.elements.reduce((sum, el) => sum + getActualDuration(el), 0)
}

function autoFillRests(voice: Voice, ts: TimeSignature): void {
  const expected = getMeasureDuration(ts)
  let remaining = expected - computeVoiceDuration(voice)
  const durations: NoteDuration[] = ['whole', 'half', 'quarter', 'eighth', 'sixteenth']

  while (remaining > 0.001) {
    let placed = false
    for (const dur of durations) {
      const val = DURATION_VALUES[dur]
      const dottedVal = val * 1.5
      if (dottedVal <= remaining + 0.0001) {
        voice.elements.push({ type: 'rest', duration: dur, dotted: true })
        remaining -= dottedVal
        placed = true
        break
      }
      if (val <= remaining + 0.0001) {
        voice.elements.push({ type: 'rest', duration: dur, dotted: false })
        remaining -= val
        placed = true
        break
      }
    }
    if (!placed) break
  }
}

export const useScoreStore = defineStore('score', () => {
  const score = ref<ScoreContent>(defaultScore())
  const scoreId = ref<number | null>(null)
  const activeStaffIndex = ref(0)
  const activeVoiceId = ref(1)
  const selectedMeasure = ref(0)
  const selectedElementIndex = ref<number | null>(null)
  const dirty = ref(false)

  const activeStaff = computed(() => score.value.staves[activeStaffIndex.value])
  const activeMeasure = computed(() => activeStaff.value?.measures[selectedMeasure.value])
  const activeVoice = computed(() => activeMeasure.value?.voices.find(v => v.voice_id === activeVoiceId.value))

  function getEffectiveTimeSignature(measureIndex: number): TimeSignature {
    const staff = activeStaff.value
    for (let i = measureIndex; i >= 0; i--) {
      if (staff.measures[i].time_signature) return staff.measures[i].time_signature!
    }
    return score.value.time_signature
  }

  function insertNote(measureIdx: number, voiceId: number, elementIdx: number, element: MusicElement): boolean {
    const staff = activeStaff.value
    const measure = staff.measures[measureIdx]
    let voice = measure.voices.find(v => v.voice_id === voiceId)
    if (!voice) {
      voice = { voice_id: voiceId, elements: [] }
      measure.voices.push(voice)
    }

    const ts = getEffectiveTimeSignature(measureIdx)
    const expected = getMeasureDuration(ts)
    const currentDur = computeVoiceDuration(voice)
    const newDur = getActualDuration(element)

    if (currentDur + newDur > expected + 0.0001) return false

    // Remove trailing rests to make room if needed
    while (voice.elements.length > 0) {
      const last = voice.elements[voice.elements.length - 1]
      if (last.type !== 'rest') break
      const lastDur = getActualDuration(last)
      if (computeVoiceDuration(voice) - lastDur + newDur <= expected + 0.0001) {
        voice.elements.pop()
        break
      }
      voice.elements.pop()
    }

    voice.elements.splice(elementIdx, 0, element)
    autoFillRests(voice, ts)
    dirty.value = true
    return true
  }

  function deleteElement(measureIdx: number, voiceId: number, elementIdx: number): void {
    const staff = activeStaff.value
    const measure = staff.measures[measureIdx]
    const voice = measure.voices.find(v => v.voice_id === voiceId)
    if (!voice || elementIdx >= voice.elements.length) return

    voice.elements.splice(elementIdx, 1)
    const ts = getEffectiveTimeSignature(measureIdx)
    autoFillRests(voice, ts)
    dirty.value = true
  }

  function addMeasure(): void {
    const staff = activeStaff.value
    const newNum = staff.measures.length + 1
    const ts = getEffectiveTimeSignature(staff.measures.length - 1)
    const restDur: NoteDuration = ts.denominator === 4 && ts.numerator === 4 ? 'whole' : 'quarter'
    const newMeasure: Measure = {
      number: newNum,
      voices: [{ voice_id: 1, elements: [] }],
      time_signature: null,
      key_signature: null,
      tempo_bpm: null,
      repeat_marks: [],
      dynamics: [],
      volta: null,
    }
    newMeasure.voices[0].elements = []
    autoFillRests(newMeasure.voices[0], ts)
    staff.measures.push(newMeasure)
    dirty.value = true
  }

  function deleteMeasure(idx: number): void {
    const staff = activeStaff.value
    if (staff.measures.length <= 1) return
    staff.measures.splice(idx, 1)
    staff.measures.forEach((m, i) => { m.number = i + 1 })
    if (selectedMeasure.value >= staff.measures.length) {
      selectedMeasure.value = staff.measures.length - 1
    }
    dirty.value = true
  }

  function setScore(newScore: ScoreContent, id: number | null = null): void {
    score.value = newScore
    scoreId.value = id
    dirty.value = false
  }

  function resetToDefault(): void {
    score.value = defaultScore()
    scoreId.value = null
    dirty.value = false
    selectedMeasure.value = 0
    selectedElementIndex.value = null
  }

  return {
    score, scoreId, dirty,
    activeStaffIndex, activeVoiceId, selectedMeasure, selectedElementIndex,
    activeStaff, activeMeasure, activeVoice,
    getEffectiveTimeSignature, insertNote, deleteElement,
    addMeasure, deleteMeasure, setScore, resetToDefault,
  }
})
