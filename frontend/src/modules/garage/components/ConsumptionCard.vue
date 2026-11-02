<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { dateShort, decimal, integer } from '@/lib/format'
import { PCard, PChart, PText } from '@/ui'

import type { Vehicle } from '../api'

const props = defineProps<{ vehicle: Vehicle }>()
const { t } = useI18n()
const stats = computed(() => props.vehicle.stats)
const points = computed(() => stats.value.recent_consumption)
const domain = computed<[number, number]>(() => {
  const values = points.value.map((p) => p.km_l)
  const min = Math.floor(Math.min(...values) - 1)
  const max = Math.ceil(Math.max(...values) + 1)
  return [Math.max(0, min), max]
})
const data = computed(() =>
  points.value.map((point, index) => ({
    label: dateShort(point.fueled_at),
    value: point.km_l,
    highlight: index === points.value.length - 1,
  })),
)
</script>

<template>
  <PCard>
    <div class="consumption__head">
      <div>
        <PText variant="sm" tone="muted" weight="semibold">{{
          t('garage.consumption.title')
        }}</PText>
        <PText variant="number-l"
          >{{ stats.avg_consumption_km_l ? decimal(stats.avg_consumption_km_l) : '—'
          }}<small> {{ t('garage.units.kmL') }}</small></PText
        >
      </div>
      <PText v-if="points.length" variant="sm" tone="muted">{{
        t('garage.consumption.recent')
      }}</PText>
    </div>
    <template v-if="points.length">
      <PChart
        type="bars"
        tone="garage"
        :label="t('garage.consumption.chart')"
        :data="data"
        :domain="domain"
        :average="
          stats.avg_consumption_km_l
            ? {
                value: stats.avg_consumption_km_l,
                label: t('garage.consumption.average', {
                  value: decimal(stats.avg_consumption_km_l),
                }),
              }
            : undefined
        "
        value-labels="all"
        :height="140"
        :format="(value) => decimal(value)"
      />
      <PText variant="xs" tone="muted">{{
        t('garage.consumption.axis', { min: integer(domain[0]), max: integer(domain[1]) })
      }}</PText>
    </template>
    <PText v-else variant="sm" tone="muted">{{ t('garage.consumption.empty') }}</PText>
  </PCard>
</template>

<style scoped>
.consumption__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-3);
}
</style>
