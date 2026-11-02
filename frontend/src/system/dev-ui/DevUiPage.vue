<script setup lang="ts">
/**
 * /dev/ui (development only): every base component in both themes side by side, plus
 * compositions of design screens. Query: `?view=components|home|states&theme=light|dark`.
 */
import { computed, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { useSessionStore } from '@/app/stores/session'
import { PText } from '@/ui'

import ComponentsShowcase from './ComponentsShowcase.vue'
import HomeComposition from './HomeComposition.vue'
import StatesComposition from './StatesComposition.vue'

const route = useRoute()
const view = computed(() => String(route.query.view ?? 'components'))
const theme = computed(() => (route.query.theme === 'dark' ? 'dark' : 'light'))
const columns = computed<('light' | 'dark')[]>(() =>
  route.query.theme === 'light' || route.query.theme === 'dark'
    ? [route.query.theme]
    : ['light', 'dark'],
)

const session = useSessionStore()
onMounted(() => {
  if (!session.user) {
    session.setUser({
      id: '00000000-0000-7000-8000-000000000000',
      username: 'henrique',
      display_name: 'Henrique Sebastião',
      is_admin: true,
      created_at: '2026-11-01T00:00:00Z',
      updated_at: '2026-11-01T00:00:00Z',
    })
  }
})

const links = [
  { view: 'components', label: 'Componentes' },
  { view: 'home', label: 'Início (composição)' },
  { view: 'states', label: 'Estados (composição)' },
]
</script>

<template>
  <div v-if="view === 'components'" class="dev">
    <header class="dev__header">
      <div>
        <PText variant="overline">Vitrine · só em desenvolvimento</PText>
        <PText as="h1" variant="h1">Componentes</PText>
      </div>
      <nav class="dev__links">
        <RouterLink v-for="link in links" :key="link.view" :to="{ query: { view: link.view } }">{{
          link.label
        }}</RouterLink>
      </nav>
    </header>
    <div class="dev__columns">
      <div v-for="column in columns" :key="column" :data-theme="column" class="dev__column">
        <PText variant="overline" class="dev__column-title">{{
          column === 'light' ? 'Tema claro' : 'Tema escuro'
        }}</PText>
        <ComponentsShowcase :theme="column" />
      </div>
    </div>
  </div>
  <div v-else :data-theme="theme" class="dev__composition">
    <HomeComposition v-if="view === 'home'" />
    <StatesComposition v-else-if="view === 'states'" />
  </div>
</template>

<style scoped>
.dev {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  gap: var(--space-6);
  padding: var(--space-8) var(--space-6);
}

.dev__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
}

.dev__links {
  display: flex;
  gap: var(--space-4);
  font-weight: var(--weight-semibold);
}

.dev__columns {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(640px, 100%), 1fr));
}

.dev__column {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  border-radius: var(--radius-2xl);
  background: var(--color-bg);
}

.dev__column-title {
  padding-left: var(--space-1);
}

.dev__composition {
  min-height: 100vh;
  background: var(--color-bg);
}
</style>
