<template>
  <div class="app">
    <header class="app-header">
      <h1>乐谱编辑器</h1>
      <div class="header-actions">
        <button @click="handleNew">新建</button>
        <button @click="handleSave">保存</button>
        <button @click="uiStore.showScoreList = true">打开</button>
        <button @click="handleExportMidi">导出 MIDI</button>
      </div>
    </header>

    <div class="editor-layout">
      <NoteToolbar />
      <div class="main-area">
        <VoicePanel />
        <ScoreCanvas />
      </div>
      <PlaybackBar />
    </div>

    <ScoreListDialog v-if="uiStore.showScoreList" @close="uiStore.showScoreList = false" />
  </div>
</template>

<script setup lang="ts">
import { useScoreStore } from './stores/scoreStore'
import { useUiStore } from './stores/uiStore'
import { createScore, updateScore, getMidiUrl } from './api/scores'
import NoteToolbar from './components/toolbar/NoteToolbar.vue'
import ScoreCanvas from './components/score/ScoreCanvas.vue'
import PlaybackBar from './components/playback/PlaybackBar.vue'
import VoicePanel from './components/voice/VoicePanel.vue'
import ScoreListDialog from './components/dialogs/ScoreListDialog.vue'

const scoreStore = useScoreStore()
const uiStore = useUiStore()

async function handleNew() {
  scoreStore.resetToDefault()
}

async function handleSave() {
  const s = scoreStore.score
  if (scoreStore.scoreId) {
    await updateScore(scoreStore.scoreId, { title: s.title, composer: s.composer, content: s })
  } else {
    const res = await createScore(s.title, s.composer, s)
    scoreStore.scoreId = res.id
  }
  scoreStore.dirty = false
}

function handleExportMidi() {
  if (!scoreStore.scoreId) {
    alert('请先保存乐谱')
    return
  }
  const url = getMidiUrl(scoreStore.scoreId)
  window.open(url, '_blank')
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; }
.app { display: flex; flex-direction: column; height: 100vh; }
.app-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 16px; background: #1a1a2e; color: white;
}
.app-header h1 { font-size: 18px; }
.header-actions { display: flex; gap: 8px; }
.header-actions button {
  padding: 6px 12px; border: none; border-radius: 4px;
  background: #4a4a6a; color: white; cursor: pointer; font-size: 13px;
}
.header-actions button:hover { background: #6a6a8a; }
.editor-layout { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.main-area { flex: 1; display: flex; overflow: hidden; }
</style>
