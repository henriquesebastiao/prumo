<script setup lang="ts">
/**
 * Charts of the design: bars (with highlight and average line), grouped bars (two series),
 * donut and stacked bar. Colors come from the tone: main color for the highlighted value, soft
 * shade for history, and the tone ramp for categories.
 */
import { computed } from 'vue'

import type { ChartDatum, Tone } from './types'

const props = withDefaults(
  defineProps<{
    type: 'bars' | 'grouped' | 'donut' | 'stacked'
    data: ChartDatum[]
    /** Accessible summary of the chart. */
    label: string
    tone?: Tone
    /** Grouped bars: series names, in the order of `values`. The second series is neutral. */
    series?: string[]
    average?: { value: number; label: string }
    /** Value range of the bars axis (defaults to 0…max). */
    domain?: [number, number]
    valueLabels?: 'all' | 'highlight' | 'none'
    height?: number
    format?: (value: number) => string
    legend?: boolean
  }>(),
  {
    tone: 'neutral',
    series: () => [],
    average: undefined,
    domain: undefined,
    valueLabels: 'none',
    height: 120,
    format: (value: number) => String(value),
    legend: false,
  },
)

const values = computed(() =>
  props.data.flatMap((datum) => datum.values ?? (datum.value === undefined ? [] : [datum.value])),
)
const range = computed<[number, number]>(() => {
  if (props.domain) return props.domain
  return [0, Math.max(1, ...values.value, props.average?.value ?? 0)]
})

function heightOf(value: number): string {
  const [min, max] = range.value
  const ratio = (value - min) / (max - min || 1)
  return `${Math.max(2, Math.min(100, ratio * 100))}%`
}

const averageBottom = computed(() => (props.average ? heightOf(props.average.value) : undefined))

const total = computed(() => props.data.reduce((sum, datum) => sum + (datum.value ?? 0), 0))
const shares = computed(() =>
  props.data.map((datum) => ((datum.value ?? 0) / (total.value || 1)) * 100),
)
const RAMP = ['var(--tone-on-container)', 'var(--tone)', 'var(--tone-soft)', 'var(--tone-softer)']
function rampColor(index: number): string {
  return RAMP[index % RAMP.length] ?? 'var(--tone)'
}

const donutBackground = computed(() => {
  let start = 0
  const stops = shares.value.map((share, index) => {
    const end = start + share
    const stop = `${rampColor(index)} ${start}% ${end}%`
    start = end
    return stop
  })
  return `conic-gradient(${stops.join(', ')})`
})

function showValue(datum: ChartDatum): boolean {
  return props.valueLabels === 'all' || (props.valueLabels === 'highlight' && !!datum.highlight)
}
</script>

<template>
  <figure class="p-chart" :data-tone="tone" role="img" :aria-label="label">
    <template v-if="type === 'bars' || type === 'grouped'">
      <div class="p-chart__bars" :style="{ height: `${height}px` }">
        <span
          v-if="average"
          class="p-chart__average"
          :style="{ bottom: averageBottom }"
          aria-hidden="true"
        >
          <span class="p-chart__average-label">{{ average.label }}</span>
        </span>
        <div
          v-for="datum in data"
          :key="datum.label"
          class="p-chart__column"
          :class="{ 'p-chart__column--on': datum.highlight }"
        >
          <template v-if="type === 'bars' && datum.value !== undefined">
            <span v-if="showValue(datum)" class="p-chart__value">{{ format(datum.value) }}</span>
            <i class="p-chart__bar" :style="{ height: heightOf(datum.value) }" />
          </template>
          <div v-else class="p-chart__group">
            <div v-for="(value, index) in datum.values ?? []" :key="index" class="p-chart__slot">
              <span v-if="showValue(datum)" class="p-chart__value">{{ format(value) }}</span>
              <i
                class="p-chart__bar"
                :class="index === 0 ? 'p-chart__bar--primary' : 'p-chart__bar--secondary'"
                :style="{ height: heightOf(value) }"
              />
            </div>
          </div>
        </div>
      </div>
      <div class="p-chart__labels" aria-hidden="true">
        <span
          v-for="datum in data"
          :key="datum.label"
          :class="{ 'p-chart__label--on': datum.highlight }"
          >{{ datum.label }}</span
        >
      </div>
    </template>

    <div v-else-if="type === 'donut'" class="p-chart__donut-row">
      <div
        class="p-chart__donut"
        :style="{ background: donutBackground, width: `${height}px`, height: `${height}px` }"
      >
        <div class="p-chart__donut-hole"><slot name="center" /></div>
      </div>
      <ul v-if="legend" class="p-chart__legend p-chart__legend--rows" aria-hidden="true">
        <li v-for="(datum, index) in data" :key="datum.label">
          <span class="p-chart__key" :style="{ background: rampColor(index) }" />
          <span class="p-chart__legend-label">{{ datum.label }}</span>
          <b>{{ format(datum.value ?? 0) }}</b>
          <span class="p-chart__share">{{ Math.round(shares[index] ?? 0) }}%</span>
        </li>
      </ul>
    </div>

    <template v-else>
      <div class="p-chart__stacked">
        <span
          v-for="(datum, index) in data"
          :key="datum.label"
          :style="{ width: `${shares[index]}%`, background: rampColor(index) }"
        />
      </div>
      <ul v-if="legend" class="p-chart__legend" aria-hidden="true">
        <li v-for="(datum, index) in data" :key="datum.label">
          <span class="p-chart__key" :style="{ background: rampColor(index) }" />
          <span class="p-chart__legend-label">{{ datum.label }}</span>
          <b>{{ format(datum.value ?? 0) }}</b>
        </li>
      </ul>
    </template>

    <figcaption class="p-sr-only">
      <ul>
        <li v-for="datum in data" :key="datum.label">
          {{ datum.label }}:
          {{ (datum.values ?? [datum.value ?? 0]).map((value) => format(value)).join(' / ') }}
        </li>
      </ul>
    </figcaption>
  </figure>
</template>

<style scoped>
.p-chart {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-2);
  margin: 0;
}

.p-chart__bars {
  position: relative;
  display: grid;
  align-items: end;
  gap: var(--space-3);
  border-bottom: 1px solid var(--color-border);
  grid-auto-columns: minmax(0, 1fr);
  grid-auto-flow: column;
}

.p-chart__column {
  display: flex;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
}

.p-chart__group {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: flex-end;
  justify-content: center;
  gap: var(--space-1-5);
}

.p-chart__slot {
  display: flex;
  height: 100%;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-1);
  max-width: 36px;
}

.p-chart__bar {
  display: block;
  width: 100%;
  max-width: 36px;
  border-radius: var(--radius-bar-top) var(--radius-bar-top) var(--radius-bar-bottom)
    var(--radius-bar-bottom);
  background: var(--tone-soft);
  transform-origin: bottom;
  animation: p-grow-y var(--duration-bars) var(--easing-standard) 0.2s both;
}

.p-chart__column--on .p-chart__bar {
  background: var(--tone);
}

.p-chart__bar--primary,
.p-chart__column--on .p-chart__bar--primary {
  background: var(--tone);
}

.p-chart__bar--secondary,
.p-chart__column--on .p-chart__bar--secondary {
  background: var(--color-text-secondary);
}

.p-chart__value {
  white-space: nowrap;
}

.p-chart__average {
  position: absolute;
  right: 0;
  left: 0;
  border-top: 1.5px dashed currentColor;
  color: var(--tone-on-container);
  opacity: 0.8;
}

.p-chart__average-label {
  position: absolute;
  right: 0;
  bottom: 2px;
  padding-left: var(--space-1-5);
  background: var(--color-surface);
  font-size: var(--text-2xs);
  font-weight: var(--weight-bold);
}

.p-chart__labels {
  display: grid;
  gap: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  text-align: center;
  grid-auto-columns: minmax(0, 1fr);
  grid-auto-flow: column;
}

.p-chart__label--on {
  color: var(--color-text);
  font-weight: var(--weight-bold);
}

.p-chart__donut-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-6);
}

.p-chart__donut {
  position: relative;
  flex: none;
  border-radius: 50%;
}

.p-chart__donut-hole {
  position: absolute;
  inset: 17%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-surface);
  line-height: 1.2;
  text-align: center;
}

.p-chart__stacked {
  display: flex;
  height: 12px;
  gap: 2px;
  overflow: hidden;
  border-radius: var(--radius-full);
}

.p-chart__stacked span {
  display: block;
  height: 100%;
}

.p-chart__legend {
  display: grid;
  gap: var(--space-1) var(--space-4);
  font-size: var(--text-sm);
  grid-template-columns: repeat(auto-fit, minmax(min(160px, 100%), 1fr));
}

.p-chart__legend--rows {
  flex: 1;
  min-width: 220px;
  gap: var(--space-2);
  grid-template-columns: 1fr;
  font-size: var(--text-md);
}

.p-chart__legend li {
  display: flex;
  align-items: center;
  gap: var(--space-1-5);
}

.p-chart__legend-label {
  flex: 1;
}

.p-chart__key {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 50%;
}

.p-chart__share {
  min-width: 3ch;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  text-align: right;
}
</style>
