<template>
  <div class="score-list-dialog" @click.self="$emit('close')">
    <div class="dialog-content">
      <h2>我的乐谱</h2>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="scores.length === 0" class="empty">暂无保存的乐谱</div>
      <ul v-else class="score-list">
        <li v-for="s in scores" :key="s.id" @click="handleOpen(s.id)">
          <span class="score-title">{{ s.title }}</span>
          <span class="score-meta">{{ s.composer }} · {{ formatDate(s.updated_at) }}</span>
        </li>
      </ul>
      <button class="close-btn" @click="$emit('close')">关闭</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listScores, getScore } from '@/api/scores'
import { useScoreStore } from '@/stores/scoreStore'
import type { ScoreListItem } from '@/types/music'

const emit = defineEmits<{ close: [] }>()
const scoreStore = useScoreStore()
const scores = ref<ScoreListItem[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    scores.value = await listScores()
  } finally {
    loading.value = false
  }
})

async function handleOpen(id: number) {
  const data = await getScore(id)
  scoreStore.setScore(data.content, data.id)
  emit('close')
}

function formatDate(s: string): string {
  return new Date(s).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.score-list-dialog {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.dialog-content {
  background: white; border-radius: 8px; padding: 24px; width: 400px; max-height: 500px; overflow: auto;
}
.dialog-content h2 { margin-bottom: 16px; }
.score-list { list-style: none; }
.score-list li {
  padding: 12px; border-bottom: 1px solid #eee; cursor: pointer;
  display: flex; flex-direction: column; gap: 4px;
}
.score-list li:hover { background: #f5f5f5; }
.score-title { font-weight: 600; }
.score-meta { font-size: 12px; color: #666; }
.close-btn { margin-top: 16px; padding: 8px 16px; border: none; border-radius: 4px; background: #eee; cursor: pointer; }
.loading, .empty { padding: 24px; text-align: center; color: #666; }
</style>
