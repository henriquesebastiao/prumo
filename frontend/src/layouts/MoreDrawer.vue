<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'

import { useSessionStore } from '@/app/stores/session'
import { PDrawer, PIcon } from '@/ui'

import type { NavItem } from './nav'

defineProps<{ items: NavItem[] }>()
const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const router = useRouter()
const session = useSessionStore()

async function logout() {
  open.value = false
  await session.logout()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <PDrawer v-model:open="open" :title="t('nav.more')">
    <nav class="more" :aria-label="t('nav.more')">
      <RouterLink
        v-for="item in items"
        :key="item.key"
        :to="item.to"
        class="more__item"
        :data-tone="item.tone"
        @click="open = false"
      >
        <PIcon :name="item.icon" class="more__icon" />
        {{ item.label }}
      </RouterLink>
      <RouterLink :to="{ name: 'settings' }" class="more__item" @click="open = false">
        <PIcon name="sliders" class="more__icon" />
        {{ t('nav.settings') }}
      </RouterLink>
      <button type="button" class="more__item" @click="logout">
        <PIcon name="logout" class="more__icon" />
        {{ t('auth.logout') }}
      </button>
    </nav>
  </PDrawer>
</template>

<style scoped>
.more {
  display: flex;
  flex-direction: column;
}

.more__item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 48px;
  padding: 0 var(--space-3);
  border: 0;
  border-radius: var(--radius-menu-item);
  background: transparent;
  color: var(--color-text);
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  text-align: left;
  text-decoration: none;
}

.more__item:hover {
  background: var(--color-surface-tint);
}

.more__item--danger {
  color: var(--color-danger);
}

.more__icon[data-tone],
.more__item[data-tone] .more__icon {
  color: var(--tone);
}
</style>
