<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { money, monthName } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PIconButton,
  PList,
  PListItem,
  PQueryState,
  PText,
  PTile,
  useToast,
} from '@/ui'

import { useArchiveCategory, useCategories, type Category, type CategoryKind } from '../api'
import CategoryForm from '../forms/CategoryForm.vue'
import { colorTone, dataIcon } from '../helpers'
import { useFinance } from './context'

const { t, te } = useI18n()
const toast = useToast()
const { month, createRequests } = useFinance()
const query = useCategories(month)
const archivedQuery = useCategories(month, 'true')
const archivedItems = computed(() => archivedQuery.data.value?.items ?? [])
const archive = useArchiveCategory()

const items = computed(() => query.data.value?.items ?? [])
const monthLabel = computed(() => {
  const name = monthName(`${month.value}-01`)
  return name.charAt(0).toLocaleUpperCase() + name.slice(1)
})
/** Each kind lists the categories used in the month; the others show on request. */
const showAll = ref<Record<CategoryKind, boolean>>({ expense: false, income: false })
const sections = computed(() =>
  (['expense', 'income'] as const).map((kind) => {
    const all = items.value.filter((category) => category.kind === kind)
    const used = all.filter(
      (category) => category.month_transactions_count > 0 || category.id === editing.value?.id,
    )
    return {
      kind,
      title: t(kind === 'expense' ? 'finance.categories.expenses' : 'finance.categories.incomes'),
      total: all.reduce((sum, category) => sum + category.month_total_cents, 0),
      list: showAll.value[kind] || used.length === 0 ? all : used,
      hidden: showAll.value[kind] || used.length === 0 ? 0 : all.length - used.length,
    }
  }),
)

/** `undefined`: closed; `null`: new category; a category: editing it. */
const editing = ref<Category | null | undefined>(undefined)
const newKind = ref<CategoryKind>('expense')
const panel = ref<HTMLElement>()
async function openForm(category: Category | null, kind: CategoryKind = 'expense') {
  editing.value = category
  newKind.value = kind
  await nextTick()
  panel.value?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
}
watch(createRequests, () => openForm(null))

async function unarchive(category: Category) {
  try {
    await archive.mutateAsync({ id: category.id, archived: false })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}
</script>

<template>
  <div class="categories" :class="{ 'categories--with-panel': editing !== undefined }">
    <div class="categories__main">
      <PQueryState :loading="query.isPending.value" :error="query.error.value">
        <PCard v-for="section in sections" :key="section.kind" :title="section.title">
          <template #actions>
            <PText variant="sm" tone="secondary" as="span">{{
              t('finance.categories.monthTotal', {
                month: monthLabel,
                value: money(section.total),
              })
            }}</PText>
          </template>
          <PList v-if="section.list.length">
            <PListItem
              v-for="category in section.list"
              :key="category.id"
              :title="category.name"
              :subtitle="
                t(
                  'finance.categories.monthCount',
                  { month: monthName(`${month}-01`) },
                  category.month_transactions_count,
                )
              "
              :current="editing?.id === category.id"
            >
              <template #leading>
                <PTile :icon="dataIcon(category.icon)" :tone="colorTone(category.color)" />
              </template>
              <template #trailing>
                <PText
                  variant="strong"
                  as="span"
                  :tone="
                    category.kind === 'income' && category.month_total_cents ? 'success' : 'default'
                  "
                  >{{ money(category.month_total_cents) }}</PText
                >
                <PBadge v-if="editing?.id === category.id" variant="solid">{{
                  t('finance.categories.editing')
                }}</PBadge>
                <PIconButton
                  v-else
                  icon="edit"
                  :label="t('finance.categories.edit', { name: category.name })"
                  @click="openForm(category)"
                />
              </template>
            </PListItem>
          </PList>
          <PText v-else variant="sm" tone="muted">{{ t('finance.categories.empty') }}</PText>
          <PButton
            v-if="section.hidden"
            variant="ghost"
            icon-right="chevron-down"
            @click="showAll[section.kind] = true"
            >{{ t('finance.categories.showUnused', section.hidden) }}</PButton
          >
        </PCard>
        <PCard v-if="archivedItems.length" :title="t('finance.categories.archived')" variant="flat">
          <PList>
            <PListItem
              v-for="category in archivedItems"
              :key="category.id"
              :title="category.name"
              :subtitle="t(`finance.categoryKinds.${category.kind}`)"
            >
              <template #leading><PTile :icon="dataIcon(category.icon)" /></template>
              <template #trailing>
                <PButton variant="ghost" icon="refresh" @click="unarchive(category)">{{
                  t('finance.actions.unarchive')
                }}</PButton>
              </template>
            </PListItem>
          </PList>
        </PCard>
      </PQueryState>
    </div>
    <div v-if="editing !== undefined" ref="panel" class="categories__panel">
      <CategoryForm
        :key="editing?.id ?? `new-${newKind}`"
        :category="editing ?? undefined"
        :kind="newKind"
        @close="editing = undefined"
      />
    </div>
  </div>
</template>

<style scoped>
.categories {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: minmax(0, 1fr);
}

.categories--with-panel {
  grid-template-columns: minmax(0, 1.68fr) minmax(0, 1fr);
}

.categories__main {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-4);
}

@media (width < 1000px) {
  .categories--with-panel {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
