import { ref } from 'vue'
import { useScoreStore } from '@/stores/scoreStore'
import { useUiStore } from '@/stores/uiStore'
import type { NoteElement, ChordElement, Pitch, NoteDuration, MusicElement } from '@/types/music'
import { DURATION_VALUES } from '@/types/music'

const TREBLE_POSITIONS: { step: string; octave: number }[] = [
  { step: 'A', octave: 5 },
  { step: 'G', octave: 5 },
  { step: 'F', octave: 5 },
  { step: 'E', octave: 5 },
  { step: 'D', octave: 5 },
  { step: 'C', octave: 5 },
  { step: 'B', octave: 4 },
  { step: 'A', octave: 4 },
  { step: 'G', octave: 4 },
  { step: 'F', octave: 4 },
  { step: 'E', octave: 4 },
  { step: 'D', octave: 4 },
  { step: 'C', octave: 4 },
]

const BASS_POSITIONS: { step: string; octave: number }[] = [
  { step: 'C', octave: 4 },
  { step: 'B', octave: 3 },
  { step: 'A', octave: 3 },
  { step: 'G', octave: 3 },
  { step: 'F', octave: 3 },
  { step: 'E', octave: 3 },
  { step: 'D', octave: 3 },
  { step: 'C', octave: 3 },
  { step: 'B', octave: 2 },
  { step: 'A', octave: 2 },
  { step: 'G', octave: 2 },
  { step: 'F', octave: 2 },
  { step: 'E', octave: 2 },
]

function getPositions(clef: string) {
  return clef === 'bass' ? BASS_POSITIONS : TREBLE_POSITIONS
}

function yToPositionIndex(y: number, staffTop: number, halfSpace: number, clef: string): number {
  const positions = getPositions(clef)
  const posFromTop = Math.round((y - staffTop) / halfSpace)
  return Math.max(0, Math.min(posFromTop, positions.length - 1))
}

const DURATION_ORDER: NoteDuration[] = ['sixteenth', 'eighth', 'quarter', 'half', 'whole']

function xDeltaToDurationChange(deltaX: number, thresholdPx: number): number {
  if (Math.abs(deltaX) < thresholdPx) return 0
  return deltaX > 0 ? 1 : -1
}

export function useNoteInput() {
  const scoreStore = useScoreStore()
  const uiStore = useUiStore()

  const isDragging = ref(false)
  const dragTarget = ref<{ measureIdx: number; voiceId: number; elementIdx: number } | null>(null)
  const dragStartY = ref(0)
  const dragStartX = ref(0)
  const dragApplied = ref(false)

  function handleStaffClick(
    event: MouseEvent,
    container: HTMLElement,
    measureIndex: number,
  ) {
    if (dragApplied.value) {
      dragApplied.value = false
      return
    }

    const rect = container.getBoundingClientRect()
    const relY = event.clientY - rect.top
    const clef = scoreStore.activeStaff.clef
    const positions = getPositions(clef)

    const staffTop = 50
    const halfSpace = 5

    const posIdx = yToPositionIndex(relY, staffTop, halfSpace, clef)
    const { step, octave } = positions[posIdx]

    if (uiStore.inputMode === 'rest') {
      const rest: MusicElement = {
        type: 'rest',
        duration: uiStore.selectedDuration,
        dotted: uiStore.dotted,
      }
      const voice = scoreStore.activeMeasure?.voices.find(v => v.voice_id === scoreStore.activeVoiceId)
      const idx = voice ? voice.elements.length : 0
      scoreStore.insertNote(measureIndex, scoreStore.activeVoiceId, idx, rest)
      return
    }

    const pitch: Pitch = {
      step,
      octave,
      accidental: uiStore.selectedAccidental,
    }

    const note: NoteElement = {
      type: 'note',
      pitch,
      duration: uiStore.selectedDuration,
      dotted: uiStore.dotted,
      articulations: [],
      dynamic: uiStore.selectedDynamic,
      velocity: 80,
    }

    const voice = scoreStore.activeMeasure?.voices.find(v => v.voice_id === scoreStore.activeVoiceId)
    const idx = voice ? voice.elements.length : 0
    scoreStore.insertNote(measureIndex, scoreStore.activeVoiceId, idx, note)
  }

  function handleDragStart(
    event: MouseEvent,
    measureIdx: number,
    voiceId: number,
    elementIdx: number,
  ) {
    const measure = scoreStore.activeStaff.measures[measureIdx]
    const voice = measure?.voices.find(v => v.voice_id === voiceId)
    if (!voice) return
    const elem = voice.elements[elementIdx]
    if (!elem || elem.type === 'rest') return

    isDragging.value = true
    dragTarget.value = { measureIdx, voiceId, elementIdx }
    dragStartY.value = event.clientY
    dragStartX.value = event.clientX
    dragApplied.value = false

    event.preventDefault()
  }

  function handleDragMove(event: MouseEvent) {
    if (!isDragging.value || !dragTarget.value) return

    const { measureIdx, voiceId, elementIdx } = dragTarget.value
    const measure = scoreStore.activeStaff.measures[measureIdx]
    const voice = measure?.voices.find(v => v.voice_id === voiceId)
    if (!voice) return
    const elem = voice.elements[elementIdx]
    if (!elem || elem.type === 'rest') return

    const deltaY = event.clientY - dragStartY.value
    const deltaX = event.clientX - dragStartX.value

    const halfSpace = 5
    const pitchSteps = Math.round(-deltaY / halfSpace)

    if (pitchSteps !== 0 && (elem.type === 'note' || elem.type === 'chord')) {
      const clef = scoreStore.activeStaff.clef
      const positions = getPositions(clef)

      if (elem.type === 'note') {
        const currentIdx = positions.findIndex(
          p => p.step === elem.pitch.step && p.octave === elem.pitch.octave
        )
        const newIdx = Math.max(0, Math.min(currentIdx - pitchSteps, positions.length - 1))
        if (newIdx !== currentIdx) {
          elem.pitch.step = positions[newIdx].step
          elem.pitch.octave = positions[newIdx].octave
          dragStartY.value = event.clientY
          dragApplied.value = true
          scoreStore.dirty = true
        }
      } else if (elem.type === 'chord' && elem.pitches.length > 0) {
        const firstPitch = elem.pitches[0]
        const currentIdx = positions.findIndex(
          p => p.step === firstPitch.step && p.octave === firstPitch.octave
        )
        const newIdx = Math.max(0, Math.min(currentIdx - pitchSteps, positions.length - 1))
        if (newIdx !== currentIdx) {
          const shift = newIdx - currentIdx
          for (const p of elem.pitches) {
            const pIdx = positions.findIndex(pos => pos.step === p.step && pos.octave === p.octave)
            const np = Math.max(0, Math.min(pIdx + shift, positions.length - 1))
            p.step = positions[np].step
            p.octave = positions[np].octave
          }
          dragStartY.value = event.clientY
          dragApplied.value = true
          scoreStore.dirty = true
        }
      }
    }

    const durationShift = xDeltaToDurationChange(deltaX, 30)
    if (durationShift !== 0 && (elem.type === 'note' || elem.type === 'chord')) {
      const currentDurIdx = DURATION_ORDER.indexOf(elem.duration)
      const newDurIdx = Math.max(0, Math.min(currentDurIdx + durationShift, DURATION_ORDER.length - 1))
      if (newDurIdx !== currentDurIdx) {
        const newDur = DURATION_ORDER[newDurIdx]
        const ts = scoreStore.getEffectiveTimeSignature(measureIdx)
        const expected = ts.numerator / ts.denominator
        const otherDuration = voice.elements.reduce((sum, el, i) => {
          if (i === elementIdx) return sum
          const base = DURATION_VALUES[el.duration]
          return sum + (el.dotted ? base * 1.5 : base)
        }, 0)
        const newElemDur = DURATION_VALUES[newDur] * (elem.dotted ? 1.5 : 1)

        if (otherDuration + newElemDur <= expected + 0.0001) {
          elem.duration = newDur
          dragStartX.value = event.clientX
          dragApplied.value = true
          scoreStore.dirty = true
        }
      }
    }
  }

  function handleDragEnd() {
    if (isDragging.value && dragApplied.value && dragTarget.value) {
      const { measureIdx, voiceId } = dragTarget.value
      const ts = scoreStore.getEffectiveTimeSignature(measureIdx)
      const measure = scoreStore.activeStaff.measures[measureIdx]
      const voice = measure?.voices.find(v => v.voice_id === voiceId)
      if (voice) {
        const current = voice.elements.reduce((sum, el) => {
          const base = DURATION_VALUES[el.duration]
          return sum + (el.dotted ? base * 1.5 : base)
        }, 0)
        const expected = ts.numerator / ts.denominator
        if (current < expected - 0.0001) {
          // Remove trailing rests and re-fill
          while (voice.elements.length > 0 && voice.elements[voice.elements.length - 1].type === 'rest') {
            voice.elements.pop()
          }
          // Trigger store to re-fill via a benign mutation
          scoreStore.dirty = true
        }
      }
    }
    isDragging.value = false
    dragTarget.value = null
  }

  return {
    handleStaffClick,
    handleDragStart,
    handleDragMove,
    handleDragEnd,
    isDragging,
  }
}
