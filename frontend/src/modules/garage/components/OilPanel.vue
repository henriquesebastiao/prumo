<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { dateShort, km } from '@/lib/format'
import { PBadge, PPanel, PProgress, PText } from '@/ui'

import type { Vehicle } from '../api'

const props = defineProps<{ oil: NonNullable<Vehicle['oil_change']> }>()
const { t } = useI18n()

interface Row {
  key: 'km' | 'date'
  label: string
  percent: number
}

const rows = computed<Row[]>(() => {
  const oil = props.oil
  const list: Row[] = []
  if (oil.remaining_km !== null && oil.used_km_percent !== null) {
    list.push({
      key: 'km',
      label:
        oil.remaining_km > 0
          ? t('garage.oil.byKm', { km: km(oil.remaining_km) })
          : t('garage.oil.byKmOver', { km: km(-oil.remaining_km) }),
      percent: oil.used_km_percent,
    })
  }
  if (oil.remaining_days !== null && oil.used_days_percent !== null) {
    const days = t('garage.oil.days', Math.abs(oil.remaining_days))
    list.push({
      key: 'date',
      label:
        oil.remaining_days < 0
          ? t('garage.oil.byDateOver', { days })
          : oil.primary === 'date' && oil.next_on
            ? t('garage.oil.byDateWhen', { days, date: dateShort(oil.next_on) })
            : t('garage.oil.byDate', { days }),
      percent: oil.used_days_percent,
    })
  }
  return list.sort((a) => (a.key === oil.primary ? -1 : 1))
})

const badge = computed(() => {
  if (props.oil.status === 'overdue')
    return { tone: 'danger', label: t('garage.oil.status.overdue') }
  if (props.oil.primary)
    return { tone: 'garage', label: t(`garage.oil.dueBy.${props.oil.primary}`) }
  return { tone: 'neutral', label: t('garage.oil.status.unknown') }
})
</script>

<template>
  <PPanel class="oil">
    <div class="oil__head">
      <PText variant="h3" as="span">{{ t('garage.oil.title') }}</PText>
      <PBadge :tone="badge.tone">{{ badge.label }}</PBadge>
    </div>
    <PText v-if="oil.status === 'unknown'" variant="sm" tone="muted">{{
      t('garage.oil.noChange')
    }}</PText>
    <div v-for="row in rows" :key="row.key" class="oil__row">
      <div class="oil__head">
        <PText variant="sm" tone="secondary" as="span">{{ row.label }}</PText>
        <PText variant="sm" weight="bold" as="span">{{ row.percent }}%</PText>
      </div>
      <PProgress
        :value="row.percent"
        :tone="
          row.key === oil.primary ? (oil.status === 'overdue' ? 'danger' : 'garage') : 'neutral'
        "
        size="sm"
        :label="row.label"
      />
    </div>
  </PPanel>
</template>

<style scoped>
.oil {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.oil__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.oil__row {
  display: flex;
  flex-direction: column;
  gap: var(--space-1-5);
}
</style>
