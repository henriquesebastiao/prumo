<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { dateShort } from '@/lib/format'
import {
  PBadge,
  PBookCover,
  PButton,
  PCard,
  PEmptyState,
  PList,
  PListItem,
  PProgress,
  PStepper,
  PText,
  useToast,
} from '@/ui'

import { coverUrl, useSaveProgress, type ReadingSummary } from '../api'
import { coverVariant } from '../helpers'

const props = defineProps<{ summary?: ReadingSummary }>()
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveProgress()
const current = computed(() => props.summary?.current ?? null)
const page = ref(0)
watch(
  () => current.value?.current_page,
  (value) => (page.value = value ?? 0),
  { immediate: true },
)

async function submit() {
  if (!current.value) return
  try {
    await save.mutateAsync({ id: current.value.book.id, page: page.value })
    toast.show({ title: t('reading.shelf.pageSaved') })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}

function shelfSubtitle(item: ReadingSummary['shelf'][number]): string {
  return item.status === 'read'
    ? item.book.author
    : t('reading.widget.pagesShort', { author: item.book.author, pages: item.total_pages })
}
</script>

<template>
  <PCard
    as="article"
    :title="t('reading.nav')"
    :subtitle="t('reading.widget.count', summary?.books_count ?? 0)"
    icon="book"
    tone="reading"
    :link-label="t('reading.actions.open')"
    :to="{ name: 'reading.home' }"
  >
    <template v-if="current">
      <div class="widget__current">
        <PBookCover
          :title="current.book.title"
          :author="current.book.author"
          :src="coverUrl({ id: current.book.id, ...current })"
          :variant="coverVariant('reading')"
          size="sm"
          :to="{ name: 'reading.book', params: { bookId: current.book.id } }"
        />
        <div class="widget__stack">
          <PText variant="sm" tone="muted">{{ t('reading.widget.readingNow') }}</PText>
          <PText variant="h2" as="h3">{{ current.book.title }}</PText>
          <PText variant="sm" tone="secondary">{{ current.book.author }}</PText>
          <div class="widget__between">
            <PText variant="sm" tone="secondary" as="span">{{
              t('reading.widget.pageOf', { page: current.current_page, total: current.total_pages })
            }}</PText>
            <PText variant="sm" weight="bold" as="span">{{ current.progress_percent }}%</PText>
          </div>
          <PProgress
            :value="current.current_page"
            :max="current.total_pages"
            tone="reading"
            :label="current.book.title"
          />
        </div>
      </div>
      <form class="widget__row" @submit.prevent="submit">
        <PStepper
          v-model="page"
          prefix="p."
          :max="current.total_pages"
          :label="t('reading.page.current')"
          class="widget__grow"
        />
        <PButton type="submit" variant="primary" :loading="save.isPending.value">{{
          t('ui.save')
        }}</PButton>
      </form>
    </template>
    <PList v-if="summary?.shelf.length">
      <PListItem
        v-for="item in summary.shelf"
        :key="item.book.id"
        :title="item.book.title"
        :subtitle="shelfSubtitle(item)"
        :to="{ name: 'reading.book', params: { bookId: item.book.id } }"
      >
        <template #trailing>
          <PBadge v-if="item.status === 'read' && item.finished_on">{{
            t('reading.widget.readOn', { date: dateShort(item.finished_on) })
          }}</PBadge>
          <PBadge v-else variant="outline">{{ t(`reading.status.${item.status}`) }}</PBadge>
        </template>
      </PListItem>
    </PList>
    <PEmptyState
      v-if="!current && !summary?.shelf.length"
      :title="t('reading.widget.empty')"
      icon="book"
      tone="reading"
    />
  </PCard>
</template>

<style scoped>
.widget__current {
  display: flex;
  align-items: stretch;
  gap: var(--space-4);
}

.widget__stack {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: var(--space-1);
}

.widget__between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-top: auto;
}

.widget__row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.widget__grow {
  min-width: 0;
  flex: 1;
}
</style>
