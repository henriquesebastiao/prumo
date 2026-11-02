<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

import type { IconName } from './icons'
import PLink from './PLink.vue'
import PTile from './PTile.vue'
import type { Tone } from './types'

withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    icon?: IconName
    tone?: Tone
    /** Link shown at the right of the header ("Abrir ›"). */
    linkLabel?: string
    to?: RouteLocationRaw
    as?: 'section' | 'article' | 'div' | 'form' | 'nav'
    headingLevel?: 2 | 3
    /** `flat`: no shadow, thin border (a card inside a card). */
    variant?: 'default' | 'flat'
    density?: 'default' | 'tight' | 'loose'
    padding?: 'sm' | 'md' | 'lg'
  }>(),
  {
    title: undefined,
    subtitle: undefined,
    icon: undefined,
    tone: 'neutral',
    linkLabel: undefined,
    to: undefined,
    as: 'section',
    headingLevel: 2,
    variant: 'default',
    density: 'default',
    padding: 'md',
  },
)
</script>

<template>
  <component
    :is="as"
    class="p-card"
    :class="[`p-card--${variant}`, `p-card--${density}`, `p-card--pad-${padding}`]"
  >
    <header v-if="title || $slots.header" class="p-card__header">
      <slot name="header">
        <PTile v-if="icon" :icon="icon" :tone="tone" />
        <div class="p-card__titles">
          <component :is="`h${headingLevel}`" class="p-card__title">{{ title }}</component>
          <p v-if="subtitle" class="p-card__subtitle">{{ subtitle }}</p>
        </div>
        <slot name="actions">
          <PLink v-if="linkLabel && to" :to="to">{{ linkLabel }}</PLink>
        </slot>
      </slot>
    </header>
    <slot />
  </component>
</template>

<style scoped>
.p-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.p-card--flat {
  border: 1px solid var(--color-divider);
  box-shadow: none;
}

.p-card--tight {
  gap: var(--space-2-5);
}

.p-card--loose {
  gap: var(--space-5);
}

.p-card--pad-sm {
  padding: var(--space-4);
}

.p-card--pad-lg {
  padding: var(--space-8);
}

.p-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.p-card__titles {
  flex: 1;
  min-width: 0;
}

.p-card__title {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-snug);
}

.p-card__subtitle {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>
