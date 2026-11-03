<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  PButton,
  PCard,
  PEmptyState,
  PMenu,
  PQueryState,
  PSelect,
  PText,
  type MenuEntry,
} from '@/ui'

import { useBooks, type Book } from '../api'
import ReadingCard from '../components/ReadingCard.vue'
import ShelfItem from '../components/ShelfItem.vue'
import BookDialog from '../forms/BookDialog.vue'
import { useReading } from './context'

const { t } = useI18n()
const { query, owned } = useReading()
const books = useBooks(() => ({
  ...(query.value ? { q: query.value } : {}),
  ...(owned.value === 'all' ? {} : { owned: owned.value === 'yes' }),
}))
const all = computed(() => books.data.value ?? [])

const lastActivity = (book: Book) => book.last_progress_at ?? book.created_at
const reading = computed(() =>
  all.value
    .filter((book) => book.status === 'reading')
    .sort((a, b) => lastActivity(b).localeCompare(lastActivity(a))),
)

const sort = ref<'added' | 'title' | 'author'>('added')
const collator = new Intl.Collator(undefined, { sensitivity: 'base' })
const wanted = computed(() => {
  const list = all.value.filter((book) => book.status === 'want_to_read')
  if (sort.value === 'title') return list.sort((a, b) => collator.compare(a.title, b.title))
  if (sort.value === 'author') return list.sort((a, b) => collator.compare(a.author, b.author))
  return list.sort((a, b) => b.created_at.localeCompare(a.created_at))
})
const sortMenu = computed<MenuEntry[]>(() =>
  (['added', 'title', 'author'] as const).map((value) => ({
    label: t(`reading.shelf.sort${value.charAt(0).toUpperCase()}${value.slice(1)}`),
    checked: sort.value === value,
    onSelect: () => (sort.value = value),
  })),
)

const finished = computed(() =>
  all.value
    .filter((book) => book.status === 'read')
    .sort((a, b) => (b.finished_on ?? '').localeCompare(a.finished_on ?? '')),
)
const years = computed(() => {
  const values = [...new Set(finished.value.map((book) => book.finished_on?.slice(0, 4) ?? ''))]
  return values.filter(Boolean).sort().reverse()
})
const year = ref<string>('latest')
const selectedYear = computed(() =>
  year.value === 'latest' ? (years.value[0] ?? 'all') : year.value,
)
const read = computed(() =>
  selectedYear.value === 'all'
    ? finished.value
    : finished.value.filter((book) => book.finished_on?.startsWith(selectedYear.value)),
)
const yearOptions = computed(() => [
  ...years.value.map((value) => ({ value, label: value })),
  { value: 'all', label: t('reading.shelf.allYears') },
])
const yearModel = computed({
  get: () => selectedYear.value,
  set: (value: string) => (year.value = value),
})

const creating = ref(false)
const filtered = computed(() => Boolean(query.value) || owned.value !== 'all')
</script>

<template>
  <PQueryState
    :loading="books.isPending.value"
    :error="books.error.value"
    :empty="all.length === 0 && !filtered"
  >
    <div class="shelf">
      <PText v-if="all.length === 0" tone="muted">{{ t('reading.shelf.noResults') }}</PText>
      <ReadingCard v-for="book in reading" :key="book.id" :book="book" />
      <div class="shelf__columns">
        <PCard>
          <template #header>
            <div class="shelf__header">
              <PText variant="h2" as="h2"
                >{{ t('reading.shelf.wantToRead') }}
                <PText variant="h2" tone="muted" as="span">· {{ wanted.length }}</PText></PText
              >
              <PMenu :items="sortMenu">
                <template #trigger>
                  <PButton variant="ghost" icon-right="chevron-down">{{
                    t('reading.shelf.sort')
                  }}</PButton>
                </template>
              </PMenu>
            </div>
          </template>
          <div v-if="wanted.length" class="shelf__list">
            <ShelfItem v-for="book in wanted" :key="book.id" :book="book" />
          </div>
          <PText v-else variant="sm" tone="muted">{{ t('reading.shelf.emptyWant') }}</PText>
        </PCard>
        <PCard>
          <template #header>
            <div class="shelf__header">
              <PText variant="h2" as="h2"
                >{{ t('reading.shelf.read') }}
                <PText variant="h2" tone="muted" as="span">· {{ read.length }}</PText></PText
              >
              <div v-if="years.length" class="shelf__year">
                <PSelect v-model="yearModel" :options="yearOptions" />
              </div>
            </div>
          </template>
          <div v-if="read.length" class="shelf__list">
            <ShelfItem v-for="book in read" :key="book.id" :book="book" />
          </div>
          <PText v-else variant="sm" tone="muted">{{ t('reading.shelf.emptyRead') }}</PText>
        </PCard>
      </div>
    </div>
    <template #empty>
      <PEmptyState
        :title="t('reading.shelf.empty')"
        :description="t('reading.shelf.emptyHint')"
        icon="book"
        tone="reading"
        variant="card"
      >
        <PButton variant="primary" icon="add" @click="creating = true">{{
          t('reading.actions.add')
        }}</PButton>
      </PEmptyState>
    </template>
  </PQueryState>
  <BookDialog v-model:open="creating" />
</template>

<style scoped>
.shelf {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.shelf__columns {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(420px, 100%), 1fr));
}

.shelf__header {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.shelf__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.shelf__year {
  width: 160px;
}
</style>
