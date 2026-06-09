import { ref } from 'vue'
import * as Tone from 'tone'
import { useScoreStore } from '@/stores/scoreStore'
import { usePlaybackStore } from '@/stores/playbackStore'
import { pitchToMidi, DURATION_VALUES } from '@/types/music'
import type { MusicElement, Voice, Measure } from '@/types/music'

export function usePlayback() {
  const scoreStore = useScoreStore()
  const playbackStore = usePlaybackStore()
  const synth = ref<Tone.PolySynth | null>(null)
  const metronomeSynth = ref<Tone.MembraneSynth | null>(null)
  let scheduledEvents: number[] = []

  function initSynth() {
    if (!synth.value) {
      synth.value = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'triangle' },
        envelope: { attack: 0.02, decay: 0.1, sustain: 0.3, release: 0.5 },
      }).toDestination()
    }
    if (!metronomeSynth.value) {
      metronomeSynth.value = new Tone.MembraneSynth({
        pitchDecay: 0.01,
        octaves: 4,
        envelope: { attack: 0.001, decay: 0.1, sustain: 0, release: 0.1 },
      }).toDestination()
      metronomeSynth.value.volume.value = -6
    }
  }

  function midiToFreq(midi: number): number {
    return 440 * Math.pow(2, (midi - 69) / 12)
  }

  function getDurationSeconds(elem: MusicElement, bpm: number): number {
    const base = DURATION_VALUES[elem.duration]
    const actual = elem.dotted ? base * 1.5 : base
    const quarterDuration = 60 / bpm
    return actual * 4 * quarterDuration
  }

  async function play() {
    await Tone.start()
    initSynth()

    Tone.getTransport().cancel()
    scheduledEvents = []
    playbackStore.clearPositions()
    Tone.getTransport().bpm.value = playbackStore.tempo

    const staff = scoreStore.score.staves[scoreStore.activeStaffIndex]
    if (!staff) return

    const startIdx = playbackStore.startFromMeasure
    const measures = staff.measures.slice(startIdx)
    const ts = scoreStore.score.time_signature
    const bpm = playbackStore.tempo

    let currentTime = 0

    for (let mIdx = 0; mIdx < measures.length; mIdx++) {
      const measure = measures[mIdx]
      const actualMeasureIdx = startIdx + mIdx

      const measureTs = measure.time_signature || ts
      const beatDuration = 60 / bpm
      const measureDuration = (measureTs.numerator / measureTs.denominator) * 4 * beatDuration

      if (playbackStore.metronomeEnabled && metronomeSynth.value) {
        for (let beat = 0; beat < measureTs.numerator; beat++) {
          const beatTime = currentTime + beat * beatDuration
          const pitch = beat === 0 ? 'C5' : 'C4'
          const capturedBeat = beat
          const id = Tone.getTransport().schedule((time) => {
            metronomeSynth.value?.triggerAttackRelease(pitch, '32n', time, capturedBeat === 0 ? 0.8 : 0.4)
          }, beatTime)
          scheduledEvents.push(id)
        }
      }

      // Schedule ALL voices in this measure
      for (const voice of measure.voices) {
        let elemTime = currentTime
        for (let eIdx = 0; eIdx < voice.elements.length; eIdx++) {
          const elem = voice.elements[eIdx]
          const dur = getDurationSeconds(elem, bpm)
          const capturedMIdx = actualMeasureIdx
          const capturedEIdx = eIdx
          const capturedVoiceId = voice.voice_id

          const id = Tone.getTransport().schedule((time) => {
            playbackStore.setVoicePosition(capturedMIdx, capturedVoiceId, capturedEIdx)

            if (elem.type === 'note' && synth.value) {
              const freq = midiToFreq(pitchToMidi(elem.pitch))
              synth.value.triggerAttackRelease(freq, dur * 0.9, time, elem.velocity / 127)
            } else if (elem.type === 'chord' && synth.value) {
              const freqs = elem.pitches.map(p => midiToFreq(pitchToMidi(p)))
              synth.value.triggerAttackRelease(freqs, dur * 0.9, time, elem.velocity / 127)
            }
          }, elemTime)
          scheduledEvents.push(id)
          elemTime += dur
        }
      }

      currentTime += measureDuration
    }

    const endId = Tone.getTransport().schedule(() => {
      if (playbackStore.loopEnabled) {
        stop()
        play()
      } else {
        stop()
      }
    }, currentTime)
    scheduledEvents.push(endId)

    Tone.getTransport().start()
    playbackStore.play()
  }

  function pause() {
    Tone.getTransport().pause()
    playbackStore.pause()
  }

  function resume() {
    Tone.getTransport().start()
    playbackStore.play()
  }

  function stop() {
    Tone.getTransport().stop()
    Tone.getTransport().cancel()
    scheduledEvents = []
    playbackStore.stop()
  }

  function setTempo(bpm: number) {
    playbackStore.tempo = bpm
    Tone.getTransport().bpm.value = bpm
  }

  return { play, pause, resume, stop, setTempo }
}
