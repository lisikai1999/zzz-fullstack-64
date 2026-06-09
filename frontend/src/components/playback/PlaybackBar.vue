<template>
  <div class="playback-bar">
    <div class="transport-controls">
      <button @click="handlePlay" :disabled="playbackStore.isPlaying && !playbackStore.isPaused">
        ▶ 播放
      </button>
      <button @click="handlePause" :disabled="!playbackStore.isPlaying || playbackStore.isPaused">
        ⏸ 暂停
      </button>
      <button @click="handleStop">⏹ 停止</button>
    </div>

    <div class="tempo-control">
      <label>速度: {{ playbackStore.tempo }} BPM</label>
      <input type="range" min="40" max="240" step="1"
        :value="playbackStore.tempo"
        @input="handleTempoChange" />
    </div>

    <div class="playback-options">
      <label class="checkbox-label">
        <input type="checkbox" v-model="playbackStore.metronomeEnabled" />
        节拍器
      </label>
      <label class="checkbox-label">
        <input type="checkbox" v-model="playbackStore.loopEnabled" />
        循环
      </label>
    </div>

    <div class="position-display">
      <label>起始小节:</label>
      <input type="number" min="0"
        :max="maxMeasure"
        v-model.number="playbackStore.startFromMeasure" />
      <span class="current-pos">
        当前: 第 {{ playbackStore.currentMeasure + 1 }} 小节
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePlaybackStore } from '@/stores/playbackStore'
import { useScoreStore } from '@/stores/scoreStore'
import { usePlayback } from '@/composables/usePlayback'

const playbackStore = usePlaybackStore()
const scoreStore = useScoreStore()
const { play, pause, resume, stop, setTempo } = usePlayback()

const maxMeasure = computed(() => {
  const staff = scoreStore.score.staves[scoreStore.activeStaffIndex]
  return staff ? staff.measures.length - 1 : 0
})

function handlePlay() {
  if (playbackStore.isPaused) {
    resume()
  } else {
    play()
  }
}

function handlePause() {
  pause()
}

function handleStop() {
  stop()
}

function handleTempoChange(event: Event) {
  const val = parseInt((event.target as HTMLInputElement).value)
  setTempo(val)
}
</script>

<style scoped>
.playback-bar {
  display: flex; align-items: center; gap: 16px;
  padding: 8px 16px; background: #2d2d2d; color: white;
  flex-shrink: 0;
}
.transport-controls { display: flex; gap: 4px; }
.transport-controls button {
  padding: 6px 12px; border: none; border-radius: 4px;
  background: #4a4a4a; color: white; cursor: pointer; font-size: 12px;
}
.transport-controls button:hover:not(:disabled) { background: #5a5a5a; }
.transport-controls button:disabled { opacity: 0.5; cursor: not-allowed; }
.tempo-control { display: flex; align-items: center; gap: 8px; }
.tempo-control label { font-size: 12px; white-space: nowrap; }
.tempo-control input[type="range"] { width: 100px; }
.playback-options { display: flex; gap: 12px; }
.checkbox-label { display: flex; align-items: center; gap: 4px; font-size: 12px; cursor: pointer; }
.position-display { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.position-display input[type="number"] { width: 50px; padding: 2px 4px; border-radius: 3px; border: 1px solid #555; background: #3a3a3a; color: white; }
.current-pos { color: #aaa; }
</style>
