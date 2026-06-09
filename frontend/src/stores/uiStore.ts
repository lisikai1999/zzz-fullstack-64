import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { NoteDuration, Accidental, DynamicMark } from '@/types/music'

export const useUiStore = defineStore('ui', () => {
  const selectedDuration = ref<NoteDuration>('quarter')
  const selectedAccidental = ref<Accidental>('none')
  const selectedDynamic = ref<DynamicMark | null>(null)
  const dotted = ref(false)
  const inputMode = ref<'note' | 'rest' | 'chord'>('note')
  const showScoreList = ref(false)
  const showExport = ref(false)

  return {
    selectedDuration, selectedAccidental, selectedDynamic,
    dotted, inputMode, showScoreList, showExport,
  }
})
