<template>
  <div
    class="score-canvas"
    ref="canvasContainer"
    @click="handleClick"
    @mousemove="handleDragMove"
    @mouseup="handleDragEnd"
    @mouseleave="handleDragEnd"
  >
    <div ref="vexflowDiv" class="vexflow-container"></div>

    <!-- Positioned drag handles overlaid on rendered notes -->
    <div
      v-for="(box, idx) in noteBoxes"
      :key="`handle-${box.measureIdx}-${box.voiceId}-${box.elementIdx}`"
      class="note-handle"
      :class="{ rest: box.isRest, dragging: isDragging }"
      :style="{
        left: box.x + 'px',
        top: box.y + 'px',
        width: box.width + 'px',
        height: box.height + 'px',
      }"
      @mousedown.stop.prevent="onElementMouseDown($event, box.measureIdx, box.voiceId, box.elementIdx)"
    ></div>

    <div class="measure-controls">
      <button class="add-measure-btn" @click.stop="scoreStore.addMeasure()">+ 添加小节</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick, computed } from 'vue'
import { useScoreStore } from '@/stores/scoreStore'
import { usePlaybackStore } from '@/stores/playbackStore'
import { useNoteInput } from '@/composables/useNoteInput'
import { useVexFlow, type NoteBox } from '@/composables/useVexFlow'

const scoreStore = useScoreStore()
const playbackStore = usePlaybackStore()
const { handleStaffClick, handleDragStart, handleDragMove, handleDragEnd, isDragging } = useNoteInput()

const canvasContainer = ref<HTMLElement | null>(null)
const vexflowDiv = ref<HTMLElement | null>(null)

const highlightMeasure = ref(-1)
const highlightElement = ref(-1)

let vexflow: ReturnType<typeof useVexFlow> | null = null
const noteBoxes = ref<NoteBox[]>([])

onMounted(() => {
  if (vexflowDiv.value) {
    vexflow = useVexFlow({
      container: vexflowDiv.value,
      score: ref(scoreStore.score) as any,
      highlightMeasure,
      highlightElement,
    })
    vexflow.render()
    noteBoxes.value = vexflow.noteBoxes as unknown as NoteBox[]
  }
})

watch(() => [scoreStore.score, scoreStore.dirty], () => {
  nextTick(() => {
    vexflow?.render()
    if (vexflow) noteBoxes.value = [...vexflow.noteBoxes]
  })
}, { deep: true })

watch(() => [playbackStore.currentMeasure, playbackStore.activePositions.size], () => {
  nextTick(() => {
    vexflow?.render()
    if (vexflow) noteBoxes.value = [...vexflow.noteBoxes]
  })
})

function handleClick(event: MouseEvent) {
  if (isDragging.value) return
  if (!canvasContainer.value) return
  const containerWidth = canvasContainer.value.clientWidth
  const measureWidth = (containerWidth - 40) / 4
  const relX = event.clientX - canvasContainer.value.getBoundingClientRect().left - 20
  const measureIdx = Math.floor(relX / measureWidth)
  const staff = scoreStore.activeStaff
  if (measureIdx >= 0 && measureIdx < staff.measures.length) {
    scoreStore.selectedMeasure = measureIdx
    handleStaffClick(event, canvasContainer.value, measureIdx)
  }
}

function onElementMouseDown(event: MouseEvent, measureIdx: number, voiceId: number, elementIdx: number) {
  handleDragStart(event, measureIdx, voiceId, elementIdx)
}
</script>

<style scoped>
.score-canvas {
  flex: 1; overflow: auto; padding: 16px; background: white;
  border: 1px solid #e0e0e0; margin: 8px; border-radius: 8px;
  cursor: crosshair; position: relative; user-select: none;
}
.vexflow-container { min-height: 300px; position: relative; }
.note-handle {
  position: absolute;
  cursor: grab;
  border-radius: 3px;
  transition: background 0.1s;
  z-index: 10;
}
.note-handle:hover {
  background: rgba(33, 150, 243, 0.15);
  outline: 1px solid rgba(33, 150, 243, 0.4);
}
.note-handle:active,
.note-handle.dragging {
  cursor: grabbing;
  background: rgba(33, 150, 243, 0.25);
}
.note-handle.rest {
  cursor: default;
  pointer-events: none;
}
.measure-controls { margin-top: 8px; text-align: center; }
.add-measure-btn {
  padding: 6px 16px; border: 1px dashed #999; border-radius: 4px;
  background: transparent; cursor: pointer; color: #666;
}
.add-measure-btn:hover { border-color: #333; color: #333; }
</style>
