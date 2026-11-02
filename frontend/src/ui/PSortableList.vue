<script setup lang="ts" generic="Item">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import PIcon from './PIcon.vue'

const props = defineProps<{
  itemKey: (item: Item) => string
  itemLabel: (item: Item) => string
  /** Accessible name of the list. */
  label: string
}>()

/** Reordered by dragging the handle, or with the arrow keys while the handle has focus. */
const items = defineModel<Item[]>({ required: true })
const { t } = useI18n()
const dragging = ref<number | null>(null)
const over = ref<number | null>(null)
const announcement = ref('')

function move(from: number, to: number) {
  if (to < 0 || to >= items.value.length || from === to) return
  const next = [...items.value]
  const [item] = next.splice(from, 1)
  if (item === undefined) return
  next.splice(to, 0, item)
  items.value = next
  announcement.value = t('ui.sortable.moved', {
    item: props.itemLabel(item),
    position: to + 1,
    total: next.length,
  })
}

function onKeydown(event: KeyboardEvent, index: number) {
  if (event.key === 'ArrowUp') {
    event.preventDefault()
    move(index, index - 1)
    focusHandle(index - 1)
  } else if (event.key === 'ArrowDown') {
    event.preventDefault()
    move(index, index + 1)
    focusHandle(index + 1)
  }
}

const handles = ref<HTMLButtonElement[]>([])
function focusHandle(index: number) {
  requestAnimationFrame(() => handles.value[index]?.focus())
}

function onDragStart(event: DragEvent, index: number) {
  dragging.value = index
  event.dataTransfer?.setData('text/plain', String(index))
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDrop(index: number) {
  if (dragging.value !== null) move(dragging.value, index)
  dragging.value = null
  over.value = null
}
</script>

<template>
  <ul class="p-sortable" :aria-label="label">
    <li
      v-for="(item, index) in items"
      :key="itemKey(item)"
      class="p-sortable__item"
      :class="{
        'p-sortable__item--dragging': dragging === index,
        'p-sortable__item--over': over === index && dragging !== index,
      }"
      @dragover.prevent="over = index"
      @dragleave="over = null"
      @drop.prevent="onDrop(index)"
    >
      <button
        ref="handles"
        type="button"
        class="p-sortable__handle"
        draggable="true"
        :aria-label="t('ui.sortable.handle', { item: itemLabel(item) })"
        :aria-describedby="`p-sortable-help`"
        @dragstart="onDragStart($event, index)"
        @dragend="dragging = null"
        @keydown="onKeydown($event, index)"
      >
        <PIcon name="drag" size="sm" />
      </button>
      <slot :item="item" :index="index" />
    </li>
  </ul>
  <p id="p-sortable-help" class="p-sr-only">{{ t('ui.sortable.instructions') }}</p>
  <p class="p-sr-only" aria-live="polite">{{ announcement }}</p>
</template>

<style scoped>
.p-sortable {
  display: flex;
  flex-direction: column;
}

.p-sortable__item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2-5) 0;
  border-top: 1px solid var(--color-divider);
}

.p-sortable__item:first-child {
  border-top: 0;
}

.p-sortable__item--dragging {
  opacity: 0.5;
}

.p-sortable__item--over {
  box-shadow: var(--shadow-drop-indicator);
}

.p-sortable__handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: var(--control-height);
  padding: 0;
  border: 0;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--color-text-muted);
  cursor: grab;
}
</style>
