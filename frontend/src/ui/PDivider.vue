<script setup lang="ts">
/** A thin line; with `label`, a line with a short text in the middle ("agora · 14:30"). */
import type { Tone } from './types'

withDefaults(defineProps<{ label?: string; tone?: Tone }>(), {
  label: undefined,
  tone: 'neutral',
})
</script>

<template>
  <div v-if="label" class="p-divider-label" role="separator" :data-tone="tone">
    <span class="p-divider-label__text">{{ label }}</span>
  </div>
  <hr v-else class="p-divider" />
</template>

<style scoped>
.p-divider {
  width: 100%;
  height: 1px;
  margin: 0;
  border: 0;
  background: var(--color-divider);
}

.p-divider-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--tone);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
}

.p-divider-label::before,
.p-divider-label::after {
  height: 2px;
  flex: 1;
  border-radius: var(--radius-full);
  background: currentColor;
  content: '';
  opacity: 0.6;
}

.p-divider-label__text {
  flex: none;
}
</style>
