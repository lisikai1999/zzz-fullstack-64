import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export interface VoicePosition {
  voiceId: number
  elementIndex: number
}

export const usePlaybackStore = defineStore('playback', () => {
  const isPlaying = ref(false)
  const isPaused = ref(false)
  const currentMeasure = ref(0)
  const currentElementIndex = ref(0)
  const tempo = ref(120)
  const metronomeEnabled = ref(false)
  const loopEnabled = ref(false)
  const loopStart = ref(0)
  const loopEnd = ref<number | null>(null)
  const startFromMeasure = ref(0)

  // Per-voice highlight positions: Map<measureIdx, VoicePosition[]>
  const activePositions = reactive<Map<number, VoicePosition[]>>(new Map())

  function play() {
    isPlaying.value = true
    isPaused.value = false
  }

  function pause() {
    isPaused.value = true
  }

  function stop() {
    isPlaying.value = false
    isPaused.value = false
    currentMeasure.value = startFromMeasure.value
    currentElementIndex.value = 0
    activePositions.clear()
  }

  function setPosition(measure: number, element: number) {
    currentMeasure.value = measure
    currentElementIndex.value = element
  }

  function setVoicePosition(measure: number, voiceId: number, elementIndex: number) {
    if (!activePositions.has(measure)) {
      activePositions.set(measure, [])
    }
    const positions = activePositions.get(measure)!
    const existing = positions.find(p => p.voiceId === voiceId)
    if (existing) {
      existing.elementIndex = elementIndex
    } else {
      positions.push({ voiceId, elementIndex })
    }
    currentMeasure.value = measure
  }

  function clearPositions() {
    activePositions.clear()
  }

  function isHighlighted(measure: number, voiceId: number, elementIndex: number): boolean {
    if (measure !== currentMeasure.value) return false
    const positions = activePositions.get(measure)
    if (!positions) return measure === currentMeasure.value && elementIndex === currentElementIndex.value
    return positions.some(p => p.voiceId === voiceId && p.elementIndex === elementIndex)
  }

  return {
    isPlaying, isPaused, currentMeasure, currentElementIndex,
    tempo, metronomeEnabled, loopEnabled, loopStart, loopEnd,
    startFromMeasure, activePositions,
    play, pause, stop, setPosition, setVoicePosition, clearPositions, isHighlighted,
  }
})
