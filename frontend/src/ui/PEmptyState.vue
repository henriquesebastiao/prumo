<script setup lang="ts">
import type { IconName } from './icons'
import PTile from './PTile.vue'
import type { Tone } from './types'

withDefaults(
  defineProps<{
    title: string
    description?: string
    icon?: IconName
    tone?: Tone
    /** `card`: the empty state is itself a card (first-use screens). */
    variant?: 'plain' | 'card'
  }>(),
  { description: undefined, icon: undefined, tone: 'neutral', variant: 'plain' },
)
</script>

<template>
  <div class="p-empty" :class="`p-empty--${variant}`">
    <PTile v-if="icon" :icon="icon" :tone="tone" size="xl" />
    <h3 class="p-empty__title">{{ title }}</h3>
    <p v-if="description" class="p-empty__description">{{ description }}</p>
    <div v-if="$slots.default" class="p-empty__actions"><slot /></div>
  </div>
</template>

<style scoped>
.p-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2-5);
  padding: var(--space-7) var(--space-5);
  text-align: center;
}

.p-empty--card {
  min-width: 0;
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.p-empty__title {
  margin-top: var(--space-1-5);
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
}

.p-empty__description {
  max-width: 340px;
  color: var(--color-text-secondary);
  text-wrap: pretty;
}

.p-empty__actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2-5);
  margin-top: var(--space-1-5);
}
</style>
