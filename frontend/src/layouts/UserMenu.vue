<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { useSessionStore } from '@/app/stores/session'
import { useThemeStore } from '@/app/stores/theme'
import type { ThemePreference } from '@/design/theme'
import { useUpdatePreferences } from '@/system/api'
import { PAvatar, PMenu, type MenuEntry } from '@/ui'

withDefaults(
  defineProps<{ side?: 'top' | 'right' | 'bottom' | 'left'; align?: 'start' | 'center' | 'end' }>(),
  { side: 'bottom', align: 'end' },
)

const { t } = useI18n()
const router = useRouter()
const session = useSessionStore()
const theme = useThemeStore()
const updatePreferences = useUpdatePreferences()

function setTheme(value: ThemePreference) {
  theme.set(value)
  updatePreferences.mutate({ theme: value })
}

async function logout() {
  await session.logout()
  await router.replace({ name: 'login' })
}

const items = computed<MenuEntry[]>(() => [
  { type: 'label', label: t('theme.label') },
  ...(['light', 'dark', 'system'] as const).map((value) => ({
    label: t(`theme.${value}`),
    icon:
      value === 'light'
        ? ('sun' as const)
        : value === 'dark'
          ? ('moon' as const)
          : ('monitor' as const),
    checked: theme.preference === value,
    onSelect: () => setTheme(value),
  })),
  { type: 'separator' },
  { label: t('nav.settings'), icon: 'settings', to: { name: 'settings' } },
  { label: t('auth.logout'), icon: 'logout', danger: true, onSelect: () => void logout() },
])
</script>

<template>
  <PMenu :items="items" :side="side" :align="align">
    <template #trigger>
      <button type="button" class="user-menu__trigger" :aria-label="t('nav.account')">
        <PAvatar :name="session.user?.display_name ?? ''" />
      </button>
    </template>
    <template #header>
      <div class="user-menu__header">
        <b>{{ session.user?.display_name }}</b>
        <span>{{ session.user?.username }}</span>
      </div>
    </template>
  </PMenu>
</template>

<style scoped>
.user-menu__trigger {
  padding: 0;
  border: 0;
  border-radius: var(--radius-avatar);
  background: transparent;
}

.user-menu__header {
  display: flex;
  flex-direction: column;
  padding: var(--space-2) var(--space-3) var(--space-1);
}

.user-menu__header span {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>
