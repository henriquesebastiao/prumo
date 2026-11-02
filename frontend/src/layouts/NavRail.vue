<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { PFab, PIcon, PIconButton, PLogo, PPopover } from '@/ui'

import type { NavItem, QuickActionSection } from './nav'
import RegisterMenu from './RegisterMenu.vue'
import UserMenu from './UserMenu.vue'

defineProps<{ items: NavItem[]; sections: QuickActionSection[] }>()
const registerOpen = defineModel<boolean>('registerOpen', { default: false })
const emit = defineEmits<{ action: [id: string] }>()
const { t } = useI18n()

function select(id: string) {
  registerOpen.value = false
  emit('action', id)
}
</script>

<template>
  <aside class="rail">
    <RouterLink :to="{ name: 'home' }" class="rail__logo" :aria-label="t('nav.homeLink')">
      <PLogo />
    </RouterLink>
    <PPopover
      v-model:open="registerOpen"
      side="right"
      align="start"
      :label="t('quickActions.title')"
      width="340px"
      initial-focus="[role='listbox']"
    >
      <template #trigger>
        <PFab
          :icon="registerOpen ? 'close' : 'add'"
          :label="t('nav.register')"
          :aria-label="t('nav.register')"
          :aria-expanded="registerOpen"
        />
      </template>
      <RegisterMenu :sections="sections" @select="select" />
    </PPopover>
    <nav class="rail__nav" :aria-label="t('nav.main')">
      <RouterLink
        v-for="item in items"
        :key="item.key"
        :to="item.to"
        class="rail__item"
        :data-tone="item.tone"
        :class="{ 'rail__item--home': item.key === 'home', 'rail__item--plain': !item.tone }"
        :aria-current="item.current ? 'page' : undefined"
      >
        <span class="rail__indicator"><PIcon :name="item.icon" /></span>
        {{ item.label }}
      </RouterLink>
    </nav>
    <span class="rail__spacer" />
    <PIconButton icon="sliders" :label="t('nav.settings')" :to="{ name: 'settings' }" />
    <UserMenu side="right" align="end" />
  </aside>
</template>

<style scoped>
.rail {
  position: sticky;
  top: 0;
  display: flex;
  width: var(--rail-width);
  height: 100dvh;
  flex: none;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4-5);
  padding: var(--space-5) var(--space-2);
}

.rail__logo {
  display: flex;
  color: var(--color-text);
}

.rail__nav {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2-5);
}

.rail__item {
  display: flex;
  width: 72px;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-decoration: none;
}

.rail__indicator {
  display: flex;
  width: 56px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-indicator);
  color: var(--tone, var(--color-text-secondary));
  transition: background-color var(--duration-fast) var(--easing-standard);
}

.rail__item--plain:not(.rail__item--home) .rail__indicator {
  color: var(--color-text-muted);
}

.rail__item:hover .rail__indicator {
  background: var(--color-fill);
}

.rail__item[aria-current='page'] {
  color: var(--color-text);
  font-weight: var(--weight-bold);
}

.rail__item[aria-current='page'] .rail__indicator {
  background: var(--tone-container, var(--color-fill));
}

.rail__item--home[aria-current='page'] .rail__indicator {
  background: var(--color-accent);
  color: var(--color-accent-contrast);
}

.rail__spacer {
  flex: 1;
}
</style>
