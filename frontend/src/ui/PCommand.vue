<script setup lang="ts">
import {
  ListboxContent,
  ListboxFilter,
  ListboxGroup,
  ListboxGroupLabel,
  ListboxItem,
  ListboxRoot,
} from 'reka-ui'
import { computed, ref } from 'vue'

import type { IconName } from './icons'
import PIcon from './PIcon.vue'
import PKbd from './PKbd.vue'
import type { Tone } from './types'

const props = defineProps<{
  groups: {
    label: string
    items: { id: string; label: string; icon?: IconName; tone?: Tone; shortcut?: string }[]
  }[]
  placeholder: string
  emptyLabel: string
}>()

const emit = defineEmits<{ select: [id: string] }>()
const search = ref('')

const filtered = computed(() => {
  const needle = search.value.trim().toLocaleLowerCase()
  return props.groups
    .map((group) => ({
      ...group,
      items: needle
        ? group.items.filter((item) => item.label.toLocaleLowerCase().includes(needle))
        : group.items,
    }))
    .filter((group) => group.items.length > 0)
})

function onSelect(value: unknown) {
  if (typeof value === 'string') emit('select', value)
}

/** Single-key shortcuts run their item while the list (not the search field) has focus. */
function onKeydown(event: KeyboardEvent) {
  if (event.target instanceof HTMLInputElement || event.metaKey || event.ctrlKey || event.altKey)
    return
  if (event.key.length !== 1) return
  const key = event.key.toLocaleUpperCase()
  const item = props.groups.flatMap((group) => group.items).find((i) => i.shortcut === key)
  if (item) {
    event.preventDefault()
    event.stopPropagation()
    emit('select', item.id)
  }
}
</script>

<template>
  <ListboxRoot
    class="p-command"
    highlight-on-hover
    selection-behavior="replace"
    @update:model-value="onSelect"
    @keydown.capture="onKeydown"
  >
    <div class="p-command__search">
      <PIcon name="search" size="sm" />
      <ListboxFilter
        v-model="search"
        class="p-command__input"
        :placeholder="placeholder"
        :aria-label="placeholder"
      />
    </div>
    <ListboxContent class="p-command__list">
      <template v-for="(group, index) in filtered" :key="group.label">
        <div v-if="index > 0" class="p-menu__separator" role="separator" />
        <ListboxGroup>
          <ListboxGroupLabel class="p-menu__label">{{ group.label }}</ListboxGroupLabel>
          <ListboxItem
            v-for="item in group.items"
            :key="item.id"
            :value="item.id"
            class="p-menu__item"
          >
            <PIcon v-if="item.icon" :name="item.icon" :data-tone="item.tone" />
            {{ item.label }}
            <PKbd v-if="item.shortcut" class="p-menu__shortcut">{{ item.shortcut }}</PKbd>
          </ListboxItem>
        </ListboxGroup>
      </template>
      <p v-if="filtered.length === 0" class="p-command__empty">{{ emptyLabel }}</p>
    </ListboxContent>
    <div v-if="$slots.footer" class="p-command__footer"><slot name="footer" /></div>
  </ListboxRoot>
</template>

<style src="./menu.css"></style>

<style scoped>
.p-command {
  display: flex;
  flex-direction: column;
}

.p-command__search {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: var(--tab-height);
  margin: var(--space-0-5) 0 var(--space-1-5);
  padding: 0 var(--space-3-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-muted);
}

.p-command__search:focus-within {
  border-color: var(--color-focus);
  box-shadow: var(--shadow-focus);
}

.p-command__input {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--color-text);
  font-size: var(--text-base);
}

.p-command__input::placeholder {
  color: var(--color-text-muted);
}

.p-command__list {
  display: flex;
  max-height: min(520px, 70vh);
  flex-direction: column;
  overflow: auto;
}

.p-command__empty {
  padding: var(--space-4) var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.p-command__footer {
  padding: var(--space-2) var(--space-3) var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}
</style>
