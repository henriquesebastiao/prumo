<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { date } from '@/lib/format'
import { PCombobox } from '@/ui'

import { useWorkshops } from '../api'
import type { WorkshopChoice } from '../helpers'

/**
 * Workshop autocomplete (G10). The value is `{ id }` for an existing workshop or `{ name }` for
 * a new one, created by the API when the maintenance is saved.
 */
const model = defineModel<WorkshopChoice | null>({ default: null })
const { t } = useI18n()
const workshops = useWorkshops()
const created = ref<string | null>(null)
const NEW = 'new:'

const options = computed(() => [
  ...(workshops.data.value ?? []).map((workshop) => ({
    value: workshop.id,
    label: workshop.name,
    description: workshop.last_maintenance_at
      ? t(
          'garage.workshops.stats',
          { date: date(workshop.last_maintenance_at) },
          workshop.maintenances_count,
        )
      : undefined,
  })),
  ...(created.value
    ? [
        {
          value: `${NEW}${created.value}`,
          label: created.value,
          description: t('garage.workshops.newOption'),
        },
      ]
    : []),
])

const value = computed({
  get: () =>
    model.value?.id ? model.value.id : model.value?.name ? `${NEW}${model.value.name}` : null,
  set: (next: string | null) => {
    if (!next) model.value = null
    else if (next.startsWith(NEW)) model.value = { name: next.slice(NEW.length) }
    else model.value = { id: next }
  },
})

watch(model, (next) => {
  if (next?.name) created.value = next.name
})

function create(term: string) {
  created.value = term
  model.value = { name: term }
}
</script>

<template>
  <PCombobox
    v-model="value"
    :options="options"
    :placeholder="t('garage.workshops.search')"
    :create-label="(term) => t('garage.workshops.create', { name: term })"
    option-icon="wrench"
    tone="garage"
    @create="create"
  />
</template>
