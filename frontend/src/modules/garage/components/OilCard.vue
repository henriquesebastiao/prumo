<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { date, integer, km } from '@/lib/format'
import { PBadge, PButton, PCard, PDescriptionList, PNote, PRing, PText } from '@/ui'

import type { Vehicle } from '../api'

const props = defineProps<{ vehicle: Vehicle }>()
const emit = defineEmits<{ register: []; edit: [] }>()
const { t } = useI18n()
const oil = computed(() => props.vehicle.oil_change)

const details = computed(() => {
  const value = oil.value
  if (!value) return []
  const interval = [
    value.interval_km ? km(value.interval_km) : null,
    value.interval_months ? t('garage.oil.months', value.interval_months) : null,
  ]
    .filter(Boolean)
    .join(` ${t('garage.oil.or')} `)
  const items = [{ label: t('garage.oil.interval'), value: interval }]
  if (value.last) {
    items.push({
      label: t('garage.oil.last'),
      value: t('garage.oil.lastValue', {
        date: date(value.last.performed_at),
        km: km(value.last.km),
      }),
    })
    if (value.last.oil_type)
      items.push({ label: t('garage.oil.oilType'), value: value.last.oil_type })
  }
  return items
})
const ringTone = computed(() => (oil.value?.status === 'overdue' ? 'danger' : 'garage'))
</script>

<template>
  <PCard :title="t('garage.oil.next')">
    <template v-if="oil?.primary" #actions>
      <PBadge :tone="oil.status === 'overdue' ? 'danger' : 'garage'" dot>{{
        oil.status === 'overdue'
          ? t('garage.oil.status.overdue')
          : t(`garage.oil.firstBy.${oil.primary}`)
      }}</PBadge>
    </template>

    <PNote v-if="!oil">{{ t('garage.oil.noInterval') }}</PNote>
    <PNote v-else-if="oil.status === 'unknown'">{{ t('garage.oil.noChange') }}</PNote>
    <div v-else class="oil__rings">
      <div v-if="oil.remaining_km !== null" class="oil__criterion">
        <PRing
          :value="oil.used_km_percent ?? 0"
          :tone="oil.primary === 'km' ? ringTone : 'neutral'"
          :size="oil.primary === 'km' ? 148 : 112"
        >
          <PText variant="number-l" as="span">{{ integer(Math.abs(oil.remaining_km)) }}</PText>
          <PText variant="xs" weight="bold" tone="secondary" as="span">{{
            t('garage.oil.kmLeft')
          }}</PText>
        </PRing>
        <div>
          <PText variant="h3">{{ t('garage.oil.byKmTitle') }}</PText>
          <PText variant="sm" tone="secondary">{{
            t('garage.oil.untilKm', { km: km(oil.next_km ?? 0) })
          }}</PText>
          <PText v-if="oil.estimated_km_on" variant="sm" tone="secondary">{{
            t('garage.oil.estimate', { date: date(oil.estimated_km_on) })
          }}</PText>
        </div>
      </div>
      <div v-if="oil.remaining_days !== null" class="oil__criterion">
        <PRing
          :value="oil.used_days_percent ?? 0"
          :tone="oil.primary === 'date' ? ringTone : 'neutral'"
          :size="oil.primary === 'date' ? 148 : 112"
        >
          <PText variant="number-l" as="span">{{ Math.abs(oil.remaining_days) }}</PText>
          <PText variant="xs" weight="bold" tone="secondary" as="span">{{
            t('garage.oil.daysLeft')
          }}</PText>
        </PRing>
        <div>
          <PText variant="h3">{{ t('garage.oil.byDateTitle') }}</PText>
          <PText variant="sm" tone="secondary">{{
            t('garage.oil.untilDate', { date: date(oil.next_on ?? '') })
          }}</PText>
        </div>
      </div>
    </div>

    <PDescriptionList v-if="details.length" :items="details" />
    <PButton v-if="oil" block @click="emit('register')">{{
      t('garage.actions.registerOilChange')
    }}</PButton>
    <PButton v-else block @click="emit('edit')">{{ t('garage.actions.edit') }}</PButton>
  </PCard>
</template>

<style scoped>
.oil__rings {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-6) var(--space-10);
}

.oil__criterion {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}
</style>
