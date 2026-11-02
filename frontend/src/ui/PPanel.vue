<script setup lang="ts">
import type { Tone } from './types'

/** Inner panel of a card (inset background). With a tone, uses the tone container. */
withDefaults(defineProps<{ tone?: Tone; padding?: 'sm' | 'md'; as?: string }>(), {
  tone: undefined,
  padding: 'md',
  as: 'div',
})
</script>

<template>
  <component :is="as" class="p-panel" :class="`p-panel--${padding}`" :data-tone="tone"
    ><slot
  /></component>
</template>

<style scoped>
.p-panel {
  min-width: 0;
  padding: var(--space-3-5);
  border-radius: var(--radius-lg);
  background: var(--color-surface-inset);
}

.p-panel--sm {
  padding: var(--space-2-5) var(--space-3-5);
  border-radius: var(--radius-md);
}

.p-panel[data-tone] {
  background: var(--tone-container);
  color: var(--tone-on-container);
}
</style>
