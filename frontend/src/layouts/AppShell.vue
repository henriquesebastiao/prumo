<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterView, useRoute } from 'vue-router'

import { useActiveModules } from '@/app/modules'
import { useApplyPreferences } from '@/app/preferences'
import { provideQuickActions } from '@/app/quick-actions'
import { findQuickAction } from '@/app/registry'
import { isEditableTarget, useMediaQuery } from '@/lib/media'
import { PDrawer, PFab } from '@/ui'

import BottomNav from './BottomNav.vue'
import MoreDrawer from './MoreDrawer.vue'
import type { NavItem, QuickActionSection } from './nav'
import NavRail from './NavRail.vue'
import RegisterMenu from './RegisterMenu.vue'

const { t } = useI18n()
const route = useRoute()
useApplyPreferences()
const { active, quickActions } = useActiveModules()
const compact = useMediaQuery('(width < 840px)')

const moduleItems = computed<NavItem[]>(() =>
  active.value.map((module) => ({
    key: module.id,
    label: t(module.nav.labelKey),
    icon: module.icon,
    to: { name: module.nav.route },
    tone: module.id,
    current: route.meta.module === module.id,
  })),
)
const homeItem = computed<NavItem>(() => ({
  key: 'home',
  label: t('nav.home'),
  icon: 'home',
  to: { name: 'home' },
  current: route.name === 'home',
}))
const railItems = computed<NavItem[]>(() => [
  homeItem.value,
  ...moduleItems.value,
  {
    key: 'modules',
    label: t('nav.modules'),
    icon: 'modules',
    to: { name: 'settings', hash: '#modulos' },
    current: false,
  },
])
/** Phones: Início, up to three modules and "Mais" (the rest goes to the drawer). */
const bottomItems = computed(() => [homeItem.value, ...moduleItems.value.slice(0, 3)])
const moreItems = computed(() => moduleItems.value.slice(3))
const moreCurrent = computed(
  () => route.name === 'settings' || moreItems.value.some((item) => item.current),
)

const sections = computed<QuickActionSection[]>(() =>
  quickActions.value.map((group) => ({
    label: t(group.module.nav.labelKey),
    items: group.actions.map((action) => ({
      id: action.id,
      label: t(action.labelKey),
      icon: action.icon,
      tone: group.module.id,
      shortcut: action.shortcut,
    })),
  })),
)

const registerOpen = ref(false)
const moreOpen = ref(false)
const actionComponent = shallowRef<ReturnType<typeof defineAsyncComponent> | null>(null)
const actionOpen = ref(false)

function runAction(id: string) {
  registerOpen.value = false
  const action = findQuickAction(active.value, id)
  if (!action) return
  actionComponent.value = defineAsyncComponent(action.component)
  actionOpen.value = true
}

provideQuickActions(runAction)

function onKeydown(event: KeyboardEvent) {
  if (event.key.toLowerCase() !== 'n' || event.metaKey || event.ctrlKey || event.altKey) return
  if (isEditableTarget(event.target)) return
  event.preventDefault()
  registerOpen.value = true
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="shell">
    <a class="shell__skip" href="#conteudo">{{ t('app.skipToContent') }}</a>
    <NavRail
      v-if="!compact"
      v-model:register-open="registerOpen"
      :items="railItems"
      :sections="sections"
      @action="runAction"
    />
    <main id="conteudo" class="shell__main" tabindex="-1">
      <div class="shell__page">
        <RouterView />
      </div>
    </main>
    <template v-if="compact">
      <PFab
        variant="floating"
        icon="add"
        :label="t('nav.register')"
        class="shell__fab"
        @click="registerOpen = true"
      />
      <BottomNav :items="bottomItems" :more-current="moreCurrent" @more="moreOpen = true" />
      <MoreDrawer v-model:open="moreOpen" :items="moreItems" />
      <PDrawer v-model:open="registerOpen" :title="t('quickActions.title')">
        <RegisterMenu :sections="sections" @select="runAction" />
      </PDrawer>
    </template>
    <component :is="actionComponent" v-if="actionComponent" v-model:open="actionOpen" />
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  min-height: 100dvh;
}

.shell__skip {
  position: absolute;
  z-index: 100;
  top: var(--space-2);
  left: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-accent);
  color: var(--color-accent-contrast);
  transform: translateY(-200%);
}

.shell__skip:focus {
  transform: none;
}

.shell__main {
  min-width: 0;
  flex: 1;
  outline: none;
}

.shell__page {
  display: flex;
  max-width: var(--page-max-width);
  flex-direction: column;
  gap: var(--space-5);
  margin: 0 auto;
  padding: var(--space-6-5) var(--space-8) var(--space-12) var(--space-2);
}

.shell__fab {
  position: fixed;
  z-index: 21;
  right: var(--space-4);
  bottom: calc(96px + env(safe-area-inset-bottom));
}

@media (width < 840px) {
  .shell__page {
    gap: var(--space-3);
    padding: var(--space-2) var(--space-4) calc(120px + env(safe-area-inset-bottom));
  }
}
</style>
