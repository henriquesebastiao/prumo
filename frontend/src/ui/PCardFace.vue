<script setup lang="ts">
/** The face of a credit card: name, closing and due days, and its color. */
import PIcon from './PIcon.vue'
import type { Tone } from './types'

withDefaults(defineProps<{ name: string; caption?: string; tone?: Tone }>(), {
  caption: undefined,
  tone: 'finance',
})
</script>

<template>
  <div class="p-card-face" :data-tone="tone">
    <div class="p-card-face__top">
      <span class="p-card-face__name">{{ name }}</span>
      <PIcon name="card" />
    </div>
    <div class="p-card-face__bottom">
      <span v-if="caption" class="p-card-face__caption">{{ caption }}</span>
      <span class="p-card-face__chip" aria-hidden="true" />
    </div>
  </div>
</template>

<style scoped>
.p-card-face {
  display: flex;
  min-width: 0;
  aspect-ratio: 1.63;
  flex-direction: column;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-radius: var(--radius-xl);
  background: var(--color-accent);
  color: var(--color-accent-contrast);
}

.p-card-face__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.p-card-face__name {
  overflow: hidden;
  font-size: var(--text-2xl);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-snug);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.p-card-face__bottom {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.p-card-face__caption {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.p-card-face__chip {
  width: 38px;
  height: 26px;
  border-radius: var(--radius-xs);
  background: var(--tone);
}
</style>
