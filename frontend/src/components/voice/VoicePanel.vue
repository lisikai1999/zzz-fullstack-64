<template>
  <div class="voice-panel">
    <h3>声部</h3>
    <div v-for="v in voices" :key="v" class="voice-item"
      :class="{ active: scoreStore.activeVoiceId === v }"
      @click="scoreStore.activeVoiceId = v">
      <span class="voice-color" :style="{ background: voiceColors[v - 1] }"></span>
      <span>声部 {{ v }}</span>
    </div>
    <button class="add-voice-btn" @click="addVoice" v-if="voices.length < 4">+ 添加声部</button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useScoreStore } from '@/stores/scoreStore'

const scoreStore = useScoreStore()

const voiceColors = ['#1a73e8', '#e8501a', '#1ae850', '#e8e01a']

const voices = computed(() => {
  const measure = scoreStore.activeMeasure
  if (!measure) return [1]
  const ids = measure.voices.map(v => v.voice_id)
  return ids.length > 0 ? ids : [1]
})

function addVoice() {
  const measure = scoreStore.activeMeasure
  if (!measure) return
  const maxId = Math.max(...measure.voices.map(v => v.voice_id), 0)
  if (maxId >= 4) return
  measure.voices.push({ voice_id: maxId + 1, elements: [] })
  const ts = scoreStore.getEffectiveTimeSignature(scoreStore.selectedMeasure)
  // Auto-fill will happen when the user adds notes
}
</script>

<style scoped>
.voice-panel {
  width: 100px; padding: 12px 8px; background: #f8f8f8;
  border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; gap: 6px;
}
.voice-panel h3 { font-size: 12px; color: #666; margin-bottom: 4px; }
.voice-item {
  display: flex; align-items: center; gap: 6px; padding: 6px 8px;
  border-radius: 4px; cursor: pointer; font-size: 12px;
}
.voice-item:hover { background: #eee; }
.voice-item.active { background: #e3f2fd; }
.voice-color { width: 10px; height: 10px; border-radius: 50%; }
.add-voice-btn {
  margin-top: 8px; padding: 4px; border: 1px dashed #ccc;
  border-radius: 4px; background: transparent; cursor: pointer;
  font-size: 11px; color: #666;
}
</style>
