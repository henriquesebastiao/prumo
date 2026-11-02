<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { EventView, ModuleDefinition } from '@/app/registry'
import type { Schemas } from '@/lib/api/client'
import { PCard, PDateBadge, PList, PListItem, PStatus, PText, PTile } from '@/ui'

/** "Vem aí" and "Atividade recente": items of every active module, described by the module. */
/** Items shown per list, like the design. */
const LIMIT = 4

const props = defineProps<{
  modules: ModuleDefinition[]
  upcoming: Schemas['UpcomingItem'][]
  activity: Schemas['ActivityItem'][]
}>()
const { t } = useI18n()

function moduleOf(id: string) {
  return props.modules.find((module) => module.id === id)
}

const upcomingViews = computed(() =>
  props.upcoming
    .flatMap((item, index) => {
      const view = moduleOf(item.module)?.describeUpcoming?.(item, t)
      return view ? [{ key: `${item.module}-${index}`, item, view }] : []
    })
    .slice(0, LIMIT),
)
const activityViews = computed(() =>
  props.activity
    .flatMap((item, index) => {
      const view: EventView | null | undefined = moduleOf(item.module)?.describeActivity?.(item, t)
      return view ? [{ key: `${item.module}-${index}`, item, view }] : []
    })
    .slice(0, LIMIT),
)
</script>

<template>
  <div v-if="upcomingViews.length || activityViews.length" class="events">
    <PCard v-if="upcomingViews.length" :title="t('home.upcoming.title')" class="events__card">
      <PList>
        <PListItem
          v-for="entry in upcomingViews"
          :key="entry.key"
          :title="entry.view.title"
          :subtitle="entry.view.subtitle"
          :to="entry.view.to"
        >
          <template #leading>
            <PDateBadge :date="entry.item.on" />
            <PStatus :tone="entry.item.module" />
          </template>
        </PListItem>
      </PList>
    </PCard>
    <PCard v-if="activityViews.length" :title="t('home.activity.title')" class="events__card">
      <PList>
        <PListItem
          v-for="entry in activityViews"
          :key="entry.key"
          :title="entry.view.title"
          :subtitle="entry.view.subtitle"
          :to="entry.view.to"
        >
          <template #leading>
            <PTile :icon="entry.view.icon ?? 'info'" :tone="entry.item.module" shape="circle" />
          </template>
          <template v-if="entry.view.value" #trailing>
            <PText variant="strong" as="span">{{ entry.view.value }}</PText>
          </template>
        </PListItem>
      </PList>
    </PCard>
  </div>
</template>

<style scoped>
.events {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: var(--space-4);
}

.events__card {
  min-width: 0;
  flex: 1 1 420px;
}
</style>
