<script setup lang="ts">
import type { IconName } from './icons'
import PIcon from './PIcon.vue'
import type { Tone } from './types'

withDefaults(
  defineProps<{
    icon: IconName
    tone?: Tone
    size?: 'md' | 'lg' | 'xl'
    /** `circle`: round, neutral background with the icon in the tone (activity lists). */
    shape?: 'square' | 'circle'
    label?: string
  }>(),
  { tone: 'neutral', size: 'md', shape: 'square', label: undefined },
)
</script>

<template>
  <span class="p-tile" :class="[`p-tile--${size}`, `p-tile--${shape}`]" :data-tone="tone">
    <PIcon :name="icon" :size="size === 'xl' ? 'xl' : size === 'lg' ? 'lg' : 'md'" :label="label" />
  </span>
</template>

<style scoped>
.p-tile {
  display: flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-tile);
  background: var(--tone-container);
  color: var(--tone);
}

.p-tile[data-tone='neutral'] {
  color: var(--color-text-secondary);
}

.p-tile--circle {
  border-radius: 50%;
  background: var(--color-surface-tint);
}

.p-tile--lg {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-tile-lg);
}

.p-tile--xl {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-tile-xl);
}
</style>
