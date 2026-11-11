<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { date } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PConfirmDialog,
  PEmptyState,
  PList,
  PListItem,
  PQueryState,
  PSelect,
  PText,
  PTile,
  useToast,
} from '@/ui'

import { useDeletePlan, usePlans, type Plan } from '../api'
import PlanDialog from '../forms/PlanDialog.vue'
import { clock, colorTone, minutes } from '../helpers'

const { t, te, tm } = useI18n()
const toast = useToast()
const plans = usePlans()
const remove = useDeletePlan()
const longs = computed(() => tm('ui.weekdays.long') as string[])

const selectedId = ref('')
const items = computed(() => plans.data.value?.items ?? [])
watch(
  items,
  (list) => {
    if (!list.some((p) => p.id === selectedId.value)) {
      selectedId.value = list.find((p) => p.state === 'current')?.id ?? list[0]?.id ?? ''
    }
  },
  { immediate: true },
)
const plan = computed(() => items.value.find((p) => p.id === selectedId.value))
/** E1: only a version that starts today or later changes; one already in force is kept. */
const editable = computed(() =>
  Boolean(plan.value && plans.data.value && plan.value.valid_from >= plans.data.value.today),
)

function versionLabel(version: Plan): string {
  if (version.state === 'current')
    return t('studies.plan.currentSince', { date: date(version.valid_from) })
  if (version.state === 'future')
    return t('studies.plan.futureFrom', { date: date(version.valid_from) })
  return t('studies.plan.pastSince', {
    from: date(version.valid_from),
    until: version.valid_until ? date(version.valid_until) : '',
  })
}
const options = computed(() => items.value.map((p) => ({ value: p.id, label: versionLabel(p) })))

/** The blocks of each weekday, in the order of their time. */
const days = computed(() =>
  longs.value.map((name, weekday) => ({
    weekday,
    name,
    blocks: (plan.value?.blocks ?? [])
      .filter((block) => block.weekdays.includes(weekday))
      .sort((a, b) => (a.starts_at ?? '99').localeCompare(b.starts_at ?? '99')),
  })),
)

const editing = ref(false)
const creating = ref(false)
const confirming = ref(false)

async function destroy() {
  if (!plan.value) return
  try {
    await remove.mutateAsync(plan.value.id)
    toast.show({ title: t('studies.plan.deleted') })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
  confirming.value = false
}
</script>

<template>
  <PQueryState
    :loading="plans.isPending.value"
    :error="plans.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <div class="plan">
      <div class="plan__toolbar">
        <PSelect
          v-if="items.length"
          v-model="selectedId"
          :options="options"
          variant="filter"
          icon="calendar"
        />
        <span class="plan__actions">
          <PButton v-if="plan && editable" variant="outline" icon="edit" @click="editing = true">{{
            t('studies.actions.editVersion')
          }}</PButton>
          <PButton
            v-if="plan && editable"
            variant="ghost"
            icon="trash"
            @click="confirming = true"
            >{{ t('studies.actions.delete') }}</PButton
          >
          <PButton variant="primary" icon="add" @click="creating = true">{{
            t(items.length ? 'studies.actions.changePlan' : 'studies.actions.newPlan')
          }}</PButton>
        </span>
      </div>
      <PEmptyState
        v-if="!items.length"
        :title="t('studies.plan.empty')"
        :description="t('studies.plan.emptyHint')"
        icon="calendar"
        tone="studies"
        variant="card"
      />
      <template v-else-if="plan">
        <PText v-if="!editable" tone="secondary" variant="sm">{{ t('studies.plan.locked') }}</PText>
        <PText v-if="!plan.blocks.length" tone="secondary">{{ t('studies.plan.noBlocks') }}</PText>
        <div class="plan__grid">
          <PCard
            v-for="day in days"
            :key="day.weekday"
            as="section"
            :title="day.name"
            :heading-level="3"
            variant="flat"
            padding="sm"
          >
            <template #actions>
              <PBadge v-if="day.blocks.length" variant="outline">{{
                t('studies.plan.perDay', {
                  minutes: minutes(day.blocks.reduce((sum, b) => sum + b.duration_minutes, 0)),
                })
              }}</PBadge>
              <PBadge v-else variant="dashed">{{ t('studies.plan.free') }}</PBadge>
            </template>
            <PList v-if="day.blocks.length">
              <PListItem
                v-for="block in day.blocks"
                :key="block.id"
                :title="block.subject.name"
                :subtitle="
                  [clock(block.starts_at), minutes(block.duration_minutes)]
                    .filter(Boolean)
                    .join(' · ')
                "
              >
                <template #leading>
                  <PTile icon="graduation-cap" :tone="colorTone(block.subject.color)" />
                </template>
              </PListItem>
            </PList>
          </PCard>
        </div>
      </template>
    </div>
  </PQueryState>
  <PlanDialog v-model:open="editing" :plan="plan" />
  <PlanDialog v-model:open="creating" :base="plan" />
  <PConfirmDialog
    v-model:open="confirming"
    :title="t('studies.plan.deleteTitle')"
    :description="t('studies.plan.deleteBody', { date: plan ? date(plan.valid_from) : '' })"
    :confirm-label="t('studies.actions.delete')"
    tone="danger"
    icon="trash"
    :loading="remove.isPending.value"
    @confirm="destroy"
  />
</template>

<style scoped>
.plan {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.plan__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.plan__actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.plan__grid {
  display: grid;
  gap: var(--space-3);
  grid-template-columns: repeat(auto-fill, minmax(min(260px, 100%), 1fr));
}
</style>
