<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { PIcon } from '@/ui'

import type { NavItem } from './nav'

defineProps<{ items: NavItem[]; moreCurrent: boolean }>()
const emit = defineEmits<{ more: [] }>()
const { t } = useI18n()
</script>

<template>
  <nav class="bottom-nav" :aria-label="t('nav.main')">
    <RouterLink
      v-for="item in items"
      :key="item.key"
      :to="item.to"
      class="bottom-nav__item"
      :class="{ 'bottom-nav__item--home': item.key === 'home' }"
      :data-tone="item.tone"
      :aria-current="item.current ? 'page' : undefined"
    >
      <span class="bottom-nav__indicator"><PIcon :name="item.icon" /></span>
      {{ item.label }}
    </RouterLink>
    <button
      type="button"
      class="bottom-nav__item"
      :aria-current="moreCurrent ? 'page' : undefined"
      @click="emit('more')"
    >
      <span class="bottom-nav__indicator"><PIcon name="modules" /></span>
      {{ t('nav.more') }}
    </button>
  </nav>
</template>

<style scoped>
.bottom-nav {
  position: fixed;
  z-index: 20;
  right: 0;
  bottom: 0;
  left: 0;
  display: grid;
  padding: var(--space-3) var(--space-1) calc(var(--space-5) + env(safe-area-inset-bottom));
  border-top: 1px solid var(--color-divider);
  background: var(--color-surface);
  grid-auto-columns: minmax(0, 1fr);
  grid-auto-flow: column;
}

.bottom-nav__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-decoration: none;
}

.bottom-nav__indicator {
  display: flex;
  width: 64px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-indicator);
  color: var(--tone, var(--color-text-secondary));
}

.bottom-nav__item[aria-current='page'] {
  color: var(--color-text);
  font-weight: var(--weight-bold);
}

.bottom-nav__item[aria-current='page'] .bottom-nav__indicator {
  background: var(--tone-container, var(--color-fill));
}

.bottom-nav__item--home[aria-current='page'] .bottom-nav__indicator {
  background: var(--color-accent);
  color: var(--color-accent-contrast);
}
</style>
