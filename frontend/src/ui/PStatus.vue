<script setup lang="ts">
import type { Tone } from './types'

withDefaults(defineProps<{ tone?: Tone }>(), { tone: 'neutral' })
</script>

<template>
  <span class="p-status" :data-tone="tone">
    <span class="p-status__dot" aria-hidden="true" />
    <slot />
  </span>
</template>

<style scoped>
.p-status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1-5);
  font-size: var(--text-sm);
}

.p-status__dot {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 50%;
  background: var(--tone);
}

.p-status[data-tone='neutral'] .p-status__dot {
  background: var(--color-neutral);
}
</style>
