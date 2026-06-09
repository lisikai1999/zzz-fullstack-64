<template>
  <div class="note-toolbar">
    <div class="toolbar-section">
      <label>模式</label>
      <div class="btn-group">
        <button :class="{ active: uiStore.inputMode === 'note' }" @click="uiStore.inputMode = 'note'">音符</button>
        <button :class="{ active: uiStore.inputMode === 'rest' }" @click="uiStore.inputMode = 'rest'">休止符</button>
        <button :class="{ active: uiStore.inputMode === 'chord' }" @click="uiStore.inputMode = 'chord'">和弦</button>
      </div>
    </div>

    <div class="toolbar-section">
      <label>时值</label>
      <div class="btn-group">
        <button v-for="d in durations" :key="d.value"
          :class="{ active: uiStore.selectedDuration === d.value }"
          @click="uiStore.selectedDuration = d.value"
          :title="d.label">
          {{ d.symbol }}
        </button>
        <button :class="{ active: uiStore.dotted }" @click="uiStore.dotted = !uiStore.dotted" title="附点">.</button>
      </div>
    </div>

    <div class="toolbar-section">
      <label>升降号</label>
      <div class="btn-group">
        <button v-for="a in accidentals" :key="a.value"
          :class="{ active: uiStore.selectedAccidental === a.value }"
          @click="uiStore.selectedAccidental = a.value">
          {{ a.symbol }}
        </button>
      </div>
    </div>

    <div class="toolbar-section">
      <label>力度</label>
      <div class="btn-group">
        <button v-for="d in dynamics" :key="d"
          :class="{ active: uiStore.selectedDynamic === d }"
          @click="uiStore.selectedDynamic = uiStore.selectedDynamic === d ? null : d">
          {{ d }}
        </button>
      </div>
    </div>

    <div class="toolbar-section">
      <label>编辑</label>
      <div class="btn-group">
        <button @click="handleDelete" title="删除选中音符">🗑 删除</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUiStore } from '@/stores/uiStore'
import { useScoreStore } from '@/stores/scoreStore'
import type { NoteDuration } from '@/types/music'

const uiStore = useUiStore()
const scoreStore = useScoreStore()

const durations = [
  { value: 'whole' as NoteDuration, symbol: '𝅝', label: '全音符' },
  { value: 'half' as NoteDuration, symbol: '𝅗𝅥', label: '二分音符' },
  { value: 'quarter' as NoteDuration, symbol: '♩', label: '四分音符' },
  { value: 'eighth' as NoteDuration, symbol: '♪', label: '八分音符' },
  { value: 'sixteenth' as NoteDuration, symbol: '𝅘𝅥𝅯', label: '十六分音符' },
]

const accidentals = [
  { value: 'none' as const, symbol: '♮' },
  { value: 'sharp' as const, symbol: '♯' },
  { value: 'flat' as const, symbol: '♭' },
]

const dynamics = ['pp', 'p', 'mp', 'mf', 'f', 'ff'] as const

function handleDelete() {
  if (scoreStore.selectedElementIndex !== null) {
    scoreStore.deleteElement(
      scoreStore.selectedMeasure,
      scoreStore.activeVoiceId,
      scoreStore.selectedElementIndex,
    )
    scoreStore.selectedElementIndex = null
  }
}
</script>

<style scoped>
.note-toolbar {
  display: flex; flex-wrap: wrap; gap: 12px; padding: 8px 16px;
  background: #fafafa; border-bottom: 1px solid #e0e0e0;
}
.toolbar-section { display: flex; align-items: center; gap: 6px; }
.toolbar-section label { font-size: 11px; color: #666; font-weight: 600; }
.btn-group { display: flex; gap: 2px; }
.btn-group button {
  padding: 4px 8px; border: 1px solid #ddd; background: white;
  border-radius: 3px; cursor: pointer; font-size: 13px; min-width: 28px;
}
.btn-group button.active { background: #1a73e8; color: white; border-color: #1a73e8; }
.btn-group button:hover:not(.active) { background: #f0f0f0; }
</style>
