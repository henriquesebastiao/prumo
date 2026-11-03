<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { errorMessage } from '@/lib/errors'
import { date, dateShort, decimal, time } from '@/lib/format'
import {
  PBadge,
  PBookCover,
  PButton,
  PCard,
  PChart,
  PConfirmDialog,
  PDescriptionList,
  PIconButton,
  PMenu,
  PQueryState,
  PRing,
  PStepper,
  PText,
  useToast,
  type MenuEntry,
} from '@/ui'

import {
  coverUrl,
  useBook,
  useBookNotes,
  useDeleteBook,
  useDeleteNote,
  useRemoveCover,
  useSaveBook,
  useSaveProgress,
  type Note,
} from '../api'
import NoteCard from '../components/NoteCard.vue'
import BookDialog from '../forms/BookDialog.vue'
import NoteDialog from '../forms/NoteDialog.vue'
import { coverVariant } from '../helpers'

const props = defineProps<{ bookId: string }>()
const { t, te } = useI18n()
const toast = useToast()
const router = useRouter()
const query = useBook(() => props.bookId)
const notes = useBookNotes(() => props.bookId)
const book = computed(() => query.data.value)

const page = ref(0)
watch(
  () => book.value?.current_page,
  (value) => (page.value = value ?? 0),
  { immediate: true },
)
const progress = useSaveProgress()
const saveBook = useSaveBook()
const removeBook = useDeleteBook()
const removeNote = useDeleteNote()
const removeCover = useRemoveCover()

async function run(action: () => Promise<unknown>, success?: string) {
  try {
    await action()
    if (success) toast.show({ title: success })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}
const savePage = (value: number) =>
  run(() => progress.mutateAsync({ id: props.bookId, page: value }), t('reading.shelf.pageSaved'))
const start = () =>
  run(() => saveBook.mutateAsync({ id: props.bookId, body: { status: 'reading' } }))

const editing = ref(false)
const noteOpen = ref(false)
const editingNote = ref<Note>()
function openNote(note?: Note) {
  editingNote.value = note
  noteOpen.value = true
}
const deleteOpen = ref(false)
const deletingNote = ref<Note>()
const deleteNoteOpen = ref(false)

const menu = computed<MenuEntry[]>(() => [
  ...(book.value?.has_cover
    ? [
        {
          label: t('reading.actions.removeCover'),
          icon: 'image' as const,
          onSelect: () => run(() => removeCover.mutateAsync(props.bookId)),
        },
      ]
    : []),
  {
    label: t('reading.actions.delete'),
    icon: 'trash',
    danger: true,
    onSelect: () => (deleteOpen.value = true),
  },
])
function noteMenu(note: Note): MenuEntry[] {
  return [
    { label: t('reading.actions.editNote'), icon: 'edit', onSelect: () => openNote(note) },
    {
      label: t('reading.actions.deleteNote'),
      icon: 'trash',
      danger: true,
      onSelect: () => {
        deletingNote.value = note
        deleteNoteOpen.value = true
      },
    },
  ]
}

async function confirmDelete() {
  await run(() => removeBook.mutateAsync(props.bookId), t('reading.detail.deleted'))
  deleteOpen.value = false
  void router.push({ name: 'reading.home' })
}
async function confirmDeleteNote() {
  const note = deletingNote.value
  if (!note) return
  await run(
    () => removeNote.mutateAsync({ bookId: props.bookId, id: note.id }),
    t('reading.detail.noteDeleted'),
  )
  deleteNoteOpen.value = false
}

const weeks = computed(() =>
  (book.value?.weekly_pages ?? []).map((week, index, all) => ({
    label: dateShort(week.week_start),
    value: week.pages,
    highlight: index === all.length - 1,
  })),
)
const paceItems = computed(() => {
  const value = book.value
  if (!value) return []
  return [
    {
      label: t('reading.detail.average'),
      value: value.pace_pages_per_day
        ? t(
            'reading.detail.averageValue',
            { n: decimal(Math.round(value.pace_pages_per_day), 0) },
            Math.round(value.pace_pages_per_day),
          )
        : t('reading.detail.none'),
    },
    {
      label: t('reading.detail.remaining'),
      value: t(
        'reading.detail.remainingValue',
        { n: value.remaining_pages },
        value.remaining_pages,
      ),
    },
    {
      label: t('reading.detail.lastUpdate'),
      value: value.last_progress_at
        ? `${dateShort(value.last_progress_at)}, ${time(value.last_progress_at)}`
        : t('reading.detail.none'),
    },
  ]
})
</script>

<template>
  <PQueryState :loading="query.isPending.value" :error="query.error.value">
    <div v-if="book" class="book">
      <div class="book__bar">
        <PButton icon="chevron-left" :to="{ name: 'reading.home' }">{{
          t('reading.detail.back')
        }}</PButton>
        <span class="book__bar-actions">
          <PButton icon="edit" @click="editing = true">{{ t('reading.actions.edit') }}</PButton>
          <PMenu :items="menu">
            <template #trigger>
              <PIconButton icon="more" :label="t('reading.actions.more')" />
            </template>
          </PMenu>
        </span>
      </div>

      <PCard as="section">
        <div class="book__hero">
          <PBookCover
            :title="book.title"
            :author="book.author"
            :src="coverUrl(book)"
            :variant="coverVariant(book.status)"
            size="lg"
          />
          <div class="book__info">
            <span
              ><PBadge :tone="book.status === 'want_to_read' ? 'neutral' : 'reading'">{{
                t(`reading.status.${book.status}`)
              }}</PBadge></span
            >
            <PText variant="h1" as="h1">{{ book.title }}</PText>
            <PText tone="secondary">{{
              t('reading.shelf.meta', { author: book.author, pages: book.total_pages })
            }}</PText>
            <span class="book__chips">
              <PBadge variant="tag">{{
                t('reading.detail.start', {
                  date: book.started_on ? date(book.started_on) : t('reading.detail.none'),
                })
              }}</PBadge>
              <PBadge variant="tag">{{
                t('reading.detail.end', {
                  date: book.finished_on ? date(book.finished_on) : t('reading.detail.none'),
                })
              }}</PBadge>
              <PBadge v-if="book.forecast_finish_on" variant="tag">{{
                t('reading.detail.forecast', { date: dateShort(book.forecast_finish_on) })
              }}</PBadge>
              <PBadge v-if="book.owned" variant="outline">{{ t('reading.shelf.owned') }}</PBadge>
            </span>
            <form
              v-if="book.status === 'reading'"
              class="book__actions"
              @submit.prevent="savePage(page)"
            >
              <div class="book__stepper">
                <PStepper
                  v-model="page"
                  prefix="p."
                  :max="book.total_pages"
                  :label="t('reading.page.current')"
                />
              </div>
              <PButton type="submit" variant="primary" :loading="progress.isPending.value">{{
                t('reading.actions.saveProgress')
              }}</PButton>
              <PButton variant="ghost" @click="savePage(book.total_pages)">{{
                t('reading.actions.markRead')
              }}</PButton>
            </form>
            <div v-else-if="book.status === 'want_to_read'" class="book__actions">
              <PButton variant="primary" :loading="saveBook.isPending.value" @click="start">{{
                t('reading.actions.start')
              }}</PButton>
            </div>
          </div>
          <PRing :value="book.progress_percent" tone="reading" :size="220">
            <PText variant="number-xl" as="span">{{ book.progress_percent }}%</PText>
            <PText tone="muted" as="span">{{
              t('reading.detail.ofTotal', { page: book.current_page, total: book.total_pages })
            }}</PText>
          </PRing>
        </div>
      </PCard>

      <div class="book__columns">
        <PCard>
          <template #header>
            <div class="book__header">
              <PText variant="h2" as="h2"
                >{{ t('reading.detail.notes') }}
                <PText variant="h2" tone="muted" as="span">· {{ book.notes_count }}</PText></PText
              >
              <PButton variant="primary" icon="add" @click="openNote()">{{
                t('reading.actions.newNote')
              }}</PButton>
            </div>
          </template>
          <div v-if="notes.data.value?.length" class="book__notes">
            <NoteCard
              v-for="note in notes.data.value"
              :key="note.id"
              :note="note"
              :menu="noteMenu(note)"
            />
          </div>
          <PText v-else variant="sm" tone="muted">{{ t('reading.detail.noNotes') }}</PText>
        </PCard>
        <PCard :title="t('reading.detail.pace')">
          <template v-if="weeks.length">
            <PChart
              type="bars"
              tone="reading"
              :label="t('reading.detail.paceLabel')"
              :data="weeks"
              value-labels="all"
              :height="180"
            />
            <PText variant="sm" tone="muted">{{ t('reading.detail.perWeek') }}</PText>
          </template>
          <PText v-else variant="sm" tone="muted">{{ t('reading.detail.noHistory') }}</PText>
          <PDescriptionList :items="paceItems" />
        </PCard>
      </div>
    </div>
  </PQueryState>
  <BookDialog v-if="book" v-model:open="editing" :book="book" />
  <NoteDialog v-if="book" v-model:open="noteOpen" :book="book" :note="editingNote" />
  <PConfirmDialog
    v-model:open="deleteOpen"
    :title="t('reading.detail.deleteTitle')"
    :description="t('reading.detail.deleteBody', { title: book?.title ?? '' })"
    :confirm-label="t('reading.actions.delete')"
    :loading="removeBook.isPending.value"
    @confirm="confirmDelete"
  />
  <PConfirmDialog
    v-model:open="deleteNoteOpen"
    :title="t('reading.detail.deleteNoteTitle')"
    :description="t('reading.detail.deleteNoteBody')"
    :confirm-label="t('reading.actions.deleteNote')"
    :loading="removeNote.isPending.value"
    @confirm="confirmDeleteNote"
  />
</template>

<style scoped>
.book {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.book__bar,
.book__header {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.book__bar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.book__hero {
  display: grid;
  align-items: center;
  gap: var(--space-6);
  grid-template-columns: auto minmax(0, 1fr) auto;
}

.book__info {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-2);
}

.book__chips,
.book__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2-5);
}

.book__actions {
  margin-top: var(--space-2);
}

.book__stepper {
  display: flex;
  width: 280px;
}

.book__columns {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: minmax(0, 1.68fr) minmax(0, 1fr);
}

.book__notes {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

@media (width < 1000px) {
  .book__hero {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .book__columns {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (width < 600px) {
  .book__hero {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
