<script setup lang="ts">
import PIcon from './PIcon.vue'
import PKbd from './PKbd.vue'

withDefaults(
  defineProps<{
    placeholder: string
    /** `button`: opens something (a search dialog). `input`: types in place. */
    as?: 'button' | 'input'
    shortcut?: string
  }>(),
  { as: 'input', shortcut: undefined },
)
const model = defineModel<string>({ default: '' })
</script>

<template>
  <button v-if="as === 'button'" type="button" class="p-search">
    <PIcon name="search" />
    <span class="p-search__text">{{ placeholder }}</span>
    <PKbd v-if="shortcut">{{ shortcut }}</PKbd>
  </button>
  <label v-else class="p-search">
    <PIcon name="search" />
    <input
      v-model="model"
      type="search"
      class="p-search__input"
      :placeholder="placeholder"
      :aria-label="placeholder"
    />
    <PKbd v-if="shortcut">{{ shortcut }}</PKbd>
  </label>
</template>

<style scoped>
.p-search {
  display: flex;
  align-items: center;
  gap: var(--space-2-5);
  min-width: 280px;
  height: var(--control-height);
  padding: 0 var(--space-3-5) 0 var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.p-search:focus-within {
  border-color: var(--color-focus);
}

.p-search__text {
  flex: 1;
  text-align: left;
}

.p-search__input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--color-text);
}

.p-search__input::placeholder {
  color: var(--color-text-muted);
}
</style>
