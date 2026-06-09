import { ref, reactive, type Ref } from 'vue'
import { Renderer, Stave, StaveNote, Voice as VFVoice, Formatter, Accidental as VFAccidental } from 'vexflow'
import type { ScoreContent } from '@/types/music'
import { usePlaybackStore } from '@/stores/playbackStore'

export interface NoteBox {
  measureIdx: number
  voiceId: number
  elementIdx: number
  x: number
  y: number
  width: number
  height: number
  isRest: boolean
}

interface RenderContext {
  container: HTMLElement
  score: Ref<ScoreContent>
  highlightMeasure: Ref<number>
  highlightElement: Ref<number>
}

const DURATION_MAP: Record<string, string> = {
  whole: 'w',
  half: 'h',
  quarter: 'q',
  eighth: '8',
  sixteenth: '16',
}

function pitchToVexKey(pitch: { step: string; octave: number; accidental: string }): string {
  return `${pitch.step}/${pitch.octave}`
}

function accidentalToVex(acc: string): string | null {
  const map: Record<string, string> = {
    sharp: '#', flat: 'b', natural: 'n', double_sharp: '##', double_flat: 'bb',
  }
  return map[acc] || null
}

export function useVexFlow({ container, score, highlightMeasure, highlightElement }: RenderContext) {
  const noteBoxes = reactive<NoteBox[]>([])

  function render() {
    if (!container) return
    container.innerHTML = ''
    noteBoxes.length = 0

    const playbackStore = usePlaybackStore()

    const renderer = new Renderer(container as HTMLDivElement, Renderer.Backends.SVG)
    const width = Math.max(container.clientWidth, 800)
    const measuresPerLine = 4
    const measureWidth = (width - 40) / measuresPerLine
    const staffHeight = 150
    const content = score.value

    if (!content.staves.length) return

    const staff = content.staves[0]
    const totalLines = Math.ceil(staff.measures.length / measuresPerLine)
    const totalHeight = totalLines * staffHeight + 60
    renderer.resize(width, totalHeight)
    const context = renderer.getContext()
    context.setFont('Arial', 10)

    for (let lineIdx = 0; lineIdx < totalLines; lineIdx++) {
      const startMeasure = lineIdx * measuresPerLine
      const endMeasure = Math.min(startMeasure + measuresPerLine, staff.measures.length)
      const y = lineIdx * staffHeight + 30

      for (let mIdx = startMeasure; mIdx < endMeasure; mIdx++) {
        const measure = staff.measures[mIdx]
        const x = 20 + (mIdx - startMeasure) * measureWidth
        const stave = new Stave(x, y, measureWidth)

        if (mIdx === startMeasure || measure.time_signature) {
          const ts = measure.time_signature || content.time_signature
          stave.addTimeSignature(`${ts.numerator}/${ts.denominator}`)
        }
        if (mIdx === 0) {
          stave.addClef(staff.clef)
        }

        stave.setContext(context).draw()

        // Build VexFlow voices, tracking which StaveNote belongs to which element
        interface NoteRef { vfNote: StaveNote; measureIdx: number; voiceId: number; elementIdx: number; isRest: boolean }
        const allNoteRefs: NoteRef[] = []
        const vfVoices: VFVoice[] = []

        for (const voice of measure.voices) {
          if (voice.elements.length === 0) continue

          const vfNotes: StaveNote[] = []
          for (let eIdx = 0; eIdx < voice.elements.length; eIdx++) {
            const elem = voice.elements[eIdx]
            let vfNote: StaveNote

            if (elem.type === 'rest') {
              const dur = DURATION_MAP[elem.duration] + (elem.dotted ? 'd' : '') + 'r'
              vfNote = new StaveNote({ keys: ['B/4'], duration: dur })
            } else if (elem.type === 'note') {
              const dur = DURATION_MAP[elem.duration] + (elem.dotted ? 'd' : '')
              const key = pitchToVexKey(elem.pitch)
              vfNote = new StaveNote({ keys: [key], duration: dur })
              const vexAcc = accidentalToVex(elem.pitch.accidental)
              if (vexAcc) {
                vfNote.addModifier(new VFAccidental(vexAcc), 0)
              }
            } else {
              const dur = DURATION_MAP[elem.duration] + (elem.dotted ? 'd' : '')
              const keys = elem.pitches.map(p => pitchToVexKey(p))
              vfNote = new StaveNote({ keys, duration: dur })
              elem.pitches.forEach((p, idx) => {
                const vexAcc = accidentalToVex(p.accidental)
                if (vexAcc) vfNote.addModifier(new VFAccidental(vexAcc), idx)
              })
            }

            const shouldHighlight = playbackStore.isHighlighted(mIdx, voice.voice_id, eIdx)
            if (shouldHighlight) {
              vfNote.setStyle({ fillStyle: '#2196F3', strokeStyle: '#2196F3' })
            }

            if (elem.dotted) {
              (vfNote as any).addDotToAll()
            }

            vfNotes.push(vfNote)
            allNoteRefs.push({ vfNote, measureIdx: mIdx, voiceId: voice.voice_id, elementIdx: eIdx, isRest: elem.type === 'rest' })
          }

          try {
            const ts = measure.time_signature || content.time_signature
            const vfVoice = new VFVoice({
              num_beats: ts.numerator,
              beat_value: ts.denominator,
            }).setStrict(false)
            vfVoice.addTickables(vfNotes)
            vfVoices.push(vfVoice)
          } catch (e) {
            console.warn(`Voice build error measure ${mIdx}, voice ${voice.voice_id}:`, e)
          }
        }

        // Format and draw: try joining first, fall back to individual formatting
        if (vfVoices.length > 0) {
          const availableWidth = measureWidth - 30
          let drawn = false

          if (vfVoices.length === 1) {
            try {
              new Formatter().joinVoices(vfVoices).format(vfVoices, availableWidth)
              vfVoices[0].draw(context, stave)
              drawn = true
            } catch (e) {
              console.warn(`Single-voice format error measure ${mIdx}:`, e)
            }
          } else {
            // Multi-voice: attempt joint formatting, fall back to individual
            try {
              new Formatter().joinVoices(vfVoices).format(vfVoices, availableWidth)
              for (const v of vfVoices) {
                v.draw(context, stave)
              }
              drawn = true
            } catch {
              // Fallback: format and draw each voice independently
              for (const v of vfVoices) {
                try {
                  new Formatter().joinVoices([v]).format([v], availableWidth)
                  v.draw(context, stave)
                } catch (e2) {
                  console.warn(`Individual voice format error measure ${mIdx}:`, e2)
                }
              }
              drawn = true
            }
          }

          // Extract bounding boxes from drawn notes
          if (drawn) {
            for (const noteRef of allNoteRefs) {
              try {
                const bb = noteRef.vfNote.getBoundingBox()
                if (bb) {
                  noteBoxes.push({
                    measureIdx: noteRef.measureIdx,
                    voiceId: noteRef.voiceId,
                    elementIdx: noteRef.elementIdx,
                    x: bb.getX(),
                    y: bb.getY(),
                    width: bb.getW(),
                    height: bb.getH(),
                    isRest: noteRef.isRest,
                  })
                }
              } catch {
                // Some notes may not have a bounding box if draw failed
              }
            }
          }
        }
      }
    }
  }

  return { render, noteBoxes }
}
