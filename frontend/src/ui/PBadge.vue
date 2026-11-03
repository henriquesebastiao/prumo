<script setup lang="ts">
import type { IconName } from './icons'
import PIcon from './PIcon.vue'
import type { Tone } from './types'

withDefaults(
  defineProps<{
    tone?: Tone
    /** `soft`: tinted. `solid`: graphite. `outline` and `dashed`: transparent. `tag`: larger, for item chips. */
    variant?: 'soft' | 'solid' | 'outline' | 'dashed' | 'tag'
    icon?: IconName
    dot?: boolean
  }>(),
  { tone: 'neutral', variant: 'soft', icon: undefined },
)
</script>

<template>
  <span class="p-badge" :class="`p-badge--${variant}`" :data-tone="tone">
    <span v-if="dot" class="p-badge__dot" aria-hidden="true" />
    <PIcon v-if="icon" :name="icon" size="sm" />
    <slot />
  </span>
</template>

<style scoped>
.p-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1-5);
  padding: 3px var(--space-2-5);
  border-radius: var(--radius-full);
  background: var(--tone-container);
  color: var(--tone-on-container);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  white-space: nowrap;
}

.p-badge[data-tone='neutral'] {
  color: var(--color-text-secondary);
}

.p-badge.p-badge--solid {
  background: var(--color-accent);
  color: var(--color-accent-contrast);
}

.p-badge--outline,
.p-badge--dashed {
  padding: 2px 9px;
  border: 1px solid var(--color-border);
  background: transparent;
}

.p-badge--dashed {
  border-style: dashed;
  border-color: var(--color-border-strong);
}

/* Item chips can hold long names: they wrap instead of overflowing narrow screens. */
.p-badge.p-badge--tag {
  display: inline-block;
  max-width: 100%;
  padding: var(--space-1) var(--space-3);
  white-space: normal;
  background: var(--color-surface-tint);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
}

.p-badge__dot {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 50%;
  background: var(--tone);
}
</style>
