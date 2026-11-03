<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { useSessionStore } from '@/app/stores/session'
import { PCard, PNavList, PPageHeader } from '@/ui'

import AppearanceSection from './AppearanceSection.vue'
import DataSection from './DataSection.vue'
import ModulesSection from './ModulesSection.vue'
import ProfileSection from './ProfileSection.vue'
import SessionsSection from './SessionsSection.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const session = useSessionStore()

async function logout() {
  await session.logout()
  await router.replace({ name: 'login' })
}

const sections = [
  { hash: '#perfil', label: 'settings.profile.title', icon: 'user' },
  { hash: '#aparencia', label: 'settings.appearance.nav', icon: 'appearance' },
  { hash: '#modulos', label: 'settings.modules.title', icon: 'modules' },
  { hash: '#sessoes', label: 'settings.sessions.title', icon: 'laptop' },
  { hash: '#dados', label: 'settings.data.title', icon: 'download' },
] as const

const navItems = computed(() => [
  ...sections.map((section, index) => ({
    key: section.hash,
    label: t(section.label),
    icon: section.icon,
    href: section.hash,
    current: route.hash ? route.hash === section.hash : index === 0,
  })),
  { type: 'separator' as const },
  {
    key: 'logout',
    label: t('auth.logout'),
    icon: 'logout' as const,
    onClick: () => void logout(),
  },
])
</script>

<template>
  <PPageHeader :overline="t('settings.overline')" :title="t('settings.title')" />
  <div class="settings">
    <PCard as="div" padding="xs" class="settings__nav">
      <PNavList :label="t('settings.sections')" :items="navItems" />
    </PCard>
    <div class="settings__sections">
      <ProfileSection id="perfil" />
      <AppearanceSection id="aparencia" />
      <ModulesSection id="modulos" />
      <SessionsSection id="sessoes" />
      <DataSection id="dados" />
    </div>
  </div>
</template>

<style scoped>
.settings {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: var(--space-4);
}

.settings__nav {
  position: sticky;
  top: var(--space-6);
  flex: 0 1 240px;
}

.settings__sections {
  display: flex;
  min-width: 0;
  flex: 1 1 640px;
  flex-direction: column;
  gap: var(--space-4);
}

.settings__sections > :deep(*) {
  scroll-margin-top: var(--space-6);
}

@media (width < 840px) {
  .settings__nav {
    position: static;
    flex-basis: 100%;
  }
}
</style>
