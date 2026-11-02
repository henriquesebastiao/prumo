<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useActiveModules } from '@/app/modules'
import type { ModuleState } from '@/app/registry'
import { errorMessage } from '@/lib/errors'
import { useUpdatePreferences } from '@/system/api'
import { PCard, PNote, PQueryState, PSortableList, PSwitch, PText, PTile, useToast } from '@/ui'

const { t, te } = useI18n()
const toast = useToast()
const { ordered, query } = useActiveModules()
const update = useUpdatePreferences()

function save(next: ModuleState[]) {
  const enabled = next.filter((state) => state.enabled).map((state) => state.definition.id)
  update.mutate(
    { enabled_modules: enabled },
    {
      onError: (error) => toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' }),
    },
  )
}

const items = computed({
  get: () => ordered.value,
  set: (next: ModuleState[]) => save(next),
})

function toggle(target: ModuleState, enabled: boolean) {
  save(ordered.value.map((state) => (state === target ? { ...state, enabled } : state)))
}
</script>

<template>
  <PCard as="section">
    <template #header>
      <div class="modules__heading">
        <PText as="h2" variant="h2">{{ t('settings.modules.title') }}</PText>
        <PText variant="sm" tone="muted">{{ t('settings.modules.description') }}</PText>
      </div>
    </template>
    <PQueryState
      :loading="query.isPending.value"
      :error="query.error.value"
      :empty="ordered.length === 0"
      @retry="query.refetch()"
    >
      <template #empty>
        <PText tone="secondary">{{ t('settings.modules.empty') }}</PText>
      </template>
      <PSortableList
        v-model="items"
        :item-key="(state) => state.definition.id"
        :item-label="(state) => t(state.definition.nav.labelKey)"
        :label="t('settings.modules.list')"
      >
        <template #default="{ item }">
          <PTile :icon="item.definition.icon" :tone="item.definition.id" />
          <span class="modules__text">
            <PText variant="h3" as="span">{{ t(item.definition.nav.labelKey) }}</PText>
            <PText
              v-if="item.definition.descriptionKey"
              variant="sm"
              tone="muted"
              as="span"
              class="modules__description"
              >{{ t(item.definition.descriptionKey) }}</PText
            >
          </span>
          <PSwitch
            :model-value="item.enabled"
            :label="t('settings.modules.toggle', { name: t(item.definition.nav.labelKey) })"
            @update:model-value="toggle(item, $event)"
          />
        </template>
      </PSortableList>
    </PQueryState>
    <PNote>{{ t('settings.modules.note') }}</PNote>
  </PCard>
</template>

<style scoped>
.modules__heading,
.modules__text {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: var(--space-0-5);
}
</style>
