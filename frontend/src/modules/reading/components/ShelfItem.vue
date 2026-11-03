<script setup lang="ts">
/** A book in "Quero ler" or "Lidos". */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { date, dateShort } from '@/lib/format'
import { PBadge, PBookCover, PButton, PPanel, PText, useToast } from '@/ui'

import { coverUrl, useSaveBook, type Book } from '../api'
import { coverVariant } from '../helpers'

const props = defineProps<{ book: Book }>()
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveBook()
const to = computed(() => ({ name: 'reading.book', params: { bookId: props.book.id } }))

const period = computed(() => {
  const { started_on: start, finished_on: end } = props.book
  if (start && end) return t('reading.shelf.period', { start: dateShort(start), end: date(end) })
  return end ? t('reading.shelf.finishedOn', { date: date(end) }) : ''
})

async function start() {
  try {
    await save.mutateAsync({ id: props.book.id, body: { status: 'reading' } })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}
</script>

<template>
  <PPanel class="shelf-item">
    <PBookCover
      :title="book.title"
      :author="book.author"
      :src="coverUrl(book)"
      :variant="coverVariant(book.status)"
      :to="to"
    />
    <div class="shelf-item__body">
      <PText variant="h2" as="h3">{{ book.title }}</PText>
      <PText variant="sm" tone="secondary">{{
        t('reading.shelf.meta', { author: book.author, pages: book.total_pages })
      }}</PText>
      <template v-if="book.status === 'read'">
        <span class="shelf-item__badges">
          <PBadge tone="reading">{{ t('reading.status.read') }}</PBadge>
          <PBadge v-if="period">{{ period }}</PBadge>
          <PBadge v-if="book.owned" variant="outline">{{ t('reading.shelf.owned') }}</PBadge>
        </span>
        <PText variant="sm" tone="muted">{{
          t('reading.shelf.notesCount', book.notes_count)
        }}</PText>
      </template>
      <template v-else>
        <PText variant="sm" tone="muted"
          >{{ t('reading.shelf.since', { date: date(book.created_at) }) }}
          <PBadge v-if="book.owned" variant="outline">{{ t('reading.shelf.owned') }}</PBadge>
        </PText>
        <span>
          <PButton :loading="save.isPending.value" @click="start">{{
            t('reading.actions.start')
          }}</PButton>
        </span>
      </template>
    </div>
  </PPanel>
</template>

<style scoped>
.shelf-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
}

.shelf-item__body {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-1-5);
}

.shelf-item__badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1-5);
  margin-top: var(--space-1);
}
</style>
