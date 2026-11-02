<script setup lang="ts">
import { computed } from 'vue'

import type { Tone } from './types'

const props = withDefaults(
  defineProps<{ value: number; tone?: Tone; size?: number; label?: string }>(),
  { tone: 'neutral', size: 92, label: undefined },
)
const offset = computed(() => 100 - Math.min(100, Math.max(0, props.value)))
</script>

<template>
  <div
    class="p-ring"
    :data-tone="tone"
    :style="{ width: `${size}px`, height: `${size}px` }"
    :role="label ? 'img' : undefined"
    :aria-label="label"
  >
    <svg viewBox="0 0 100 100" aria-hidden="true">
      <circle class="p-ring__track" cx="50" cy="50" r="42" />
      <circle
        class="p-ring__fill"
        cx="50"
        cy="50"
        r="42"
        pathLength="100"
        :stroke-dashoffset="offset"
      />
    </svg>
    <div class="p-ring__center"><slot /></div>
  </div>
</template>

<style scoped>
.p-ring {
  position: relative;
  flex: none;
}

.p-ring svg {
  display: block;
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.p-ring circle {
  fill: none;
  stroke-width: 10;
}

.p-ring__track {
  stroke: var(--tone-container);
}

.p-ring__fill {
  stroke: var(--tone);
  stroke-dasharray: 100;
  stroke-linecap: round;
  animation: p-ring var(--duration-ring) var(--easing-standard) 0.2s both;
}

.p-ring[data-tone='neutral'] .p-ring__track {
  stroke: var(--color-fill);
}

.p-ring[data-tone='neutral'] .p-ring__fill {
  stroke: var(--color-neutral);
}

.p-ring__center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1.1;
  text-align: center;
}
</style>
