<script setup lang="ts">
import { computed } from 'vue'

import type { Tone } from './types'

const props = withDefaults(
  defineProps<{
    value: number
    max?: number
    tone?: Tone
    size?: 'sm' | 'md' | 'lg'
    label?: string
    /** Fill with the darker "text" shade of the tone (for example the finance expense bar). */
    strong?: boolean
  }>(),
  { max: 100, tone: 'neutral', size: 'md', label: undefined },
)

const percent = computed(() => Math.min(100, Math.max(0, (props.value / props.max) * 100)))
</script>

<template>
  <div
    class="p-progress"
    :class="[`p-progress--${size}`, { 'p-progress--strong': strong }]"
    :data-tone="tone"
    role="progressbar"
    :aria-valuenow="Math.round(percent)"
    aria-valuemin="0"
    aria-valuemax="100"
    :aria-label="label"
  >
    <span class="p-progress__fill" :style="{ width: `${percent}%` }" />
  </div>
</template>

<style scoped>
.p-progress {
  height: 8px;
  overflow: hidden;
  border-radius: var(--radius-full);
  background: var(--color-fill);
}

.p-progress--sm {
  height: 6px;
}

.p-progress--lg {
  height: 12px;
}

.p-progress__fill {
  display: block;
  height: 100%;
  border-radius: var(--radius-full);
  background: var(--tone);
  transform-origin: left;
  animation: p-grow-x var(--duration-draw) var(--easing-standard) 0.2s both;
}

.p-progress--strong .p-progress__fill {
  background: var(--tone-on-container);
}

.p-progress[data-tone='neutral'] .p-progress__fill {
  background: var(--color-neutral);
}
</style>
