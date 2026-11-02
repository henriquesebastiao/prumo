<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { useI18n } from 'vue-i18n'

import { useActiveModules } from '@/app/modules'
import { useRunQuickAction } from '@/app/quick-actions'
import { useSessionStore } from '@/app/stores/session'
import { dayPeriod, weekdayDate } from '@/lib/format'
import { useMediaQuery } from '@/lib/media'
import { installedModules } from '@/modules'
import { useDashboard } from '@/system/api'
import { PButton, PCard, PEmptyState, PPageHeader, PQueryState } from '@/ui'

const { t } = useI18n()
const session = useSessionStore()
const compact = useMediaQuery('(width < 840px)')
const { active, query: modulesQuery } = useActiveModules()
const dashboard = useDashboard()
const runQuickAction = useRunQuickAction()

const now = new Date()
const firstName = computed(() => session.user?.display_name.split(/\s+/)[0] ?? '')
const greeting = computed(() => t(`home.greeting.${dayPeriod(now)}`, { name: firstName.value }))
const overline = computed(() => weekdayDate(now, !compact.value))

const pinned = computed(() =>
  active.value.flatMap((module) =>
    (module.quickActions ?? [])
      .filter((action) => action.pinned)
      .map((action) => ({ ...action, tone: module.id })),
  ),
)

const widgets = computed(() =>
  active.value
    .filter((module) => module.dashboardWidget)
    .map((module) => ({
      id: module.id,
      component: defineAsyncComponent(module.dashboardWidget!),
      summary: dashboard.data.value?.modules.find((summary) => summary.module === module.id),
    })),
)

const loading = computed(() => modulesQuery.isPending.value || dashboard.isPending.value)
const error = computed(() => modulesQuery.error.value ?? dashboard.error.value)

function retry() {
  void modulesQuery.refetch()
  void dashboard.refetch()
}
</script>

<template>
  <PPageHeader :overline="overline" :title="greeting" :size="compact ? 'sm' : 'md'" />

  <div v-if="pinned.length" class="home__chips" role="group" :aria-label="t('quickActions.region')">
    <PButton
      v-for="action in pinned"
      :key="action.id"
      variant="chip"
      :icon="action.icon"
      :icon-tone="action.tone"
      @click="runQuickAction(action.id)"
      >{{ t(action.labelKey) }}</PButton
    >
  </div>

  <PQueryState
    :loading="loading"
    :error="error"
    :error-title="t('home.loadFailed')"
    :empty="widgets.length === 0"
    @retry="retry"
  >
    <template #empty>
      <PCard>
        <PEmptyState
          v-if="installedModules.length === 0"
          icon="modules"
          :title="t('home.noModules.title')"
          :description="t('home.noModules.description')"
        />
        <PEmptyState
          v-else
          icon="modules"
          :title="t('home.allDisabled.title')"
          :description="t('home.allDisabled.description')"
        >
          <PButton variant="primary" :to="{ name: 'settings', hash: '#modulos' }">{{
            t('home.allDisabled.action')
          }}</PButton>
        </PEmptyState>
      </PCard>
    </template>
    <div class="home__grid">
      <component
        :is="widget.component"
        v-for="widget in widgets"
        :key="widget.id"
        :summary="widget.summary"
      />
    </div>
  </PQueryState>
</template>

<style scoped>
.home__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.home__grid {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr));
}

@media (width < 840px) {
  .home__chips {
    flex-wrap: nowrap;
    margin: 0 calc(var(--space-4) * -1);
    padding: var(--space-0-5) var(--space-4) var(--space-1);
    overflow-x: auto;
  }

  .home__chips > * {
    flex: none;
  }
}
</style>
