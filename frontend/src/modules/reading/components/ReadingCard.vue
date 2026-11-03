<script setup lang="ts">
/** The book being read: progress, pace and the page stepper (Estante). */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { date, dateShort, decimal } from '@/lib/format'
import {
  PBadge,
  PBookCover,
  PButton,
  PCard,
  PLink,
  PProgress,
  PStepper,
  PText,
  useToast,
} from '@/ui'

import { coverUrl, useSaveProgress, type Book } from '../api'
import { coverVariant } from '../helpers'

const props = defineProps<{ book: Book }>()
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveProgress()
const page = ref(props.book.current_page)
watch(
  () => props.book.current_page,
  (value) => (page.value = value),
)
const to = computed(() => ({ name: 'reading.book', params: { bookId: props.book.id } }))

async function submit() {
  try {
    await save.mutateAsync({ id: props.book.id, page: page.value })
    toast.show({ title: t('reading.shelf.pageSaved') })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}
</script>

<template>
  <PCard as="article" class="reading-card">
    <div class="reading-card__grid">
      <PBookCover
        :title="book.title"
        :author="book.author"
        :src="coverUrl(book)"
        :variant="coverVariant(book.status)"
        size="lg"
        :to="to"
      />
      <div class="reading-card__info">
        <span
          ><PBadge tone="reading">{{ t('reading.shelf.readingNow') }}</PBadge></span
        >
        <PText variant="title" as="h2">{{ book.title }}</PText>
        <PText tone="secondary">
          {{ t('reading.shelf.meta', { author: book.author, pages: book.total_pages }) }}
          <template v-if="book.started_on">
            · {{ t('reading.shelf.started', { date: date(book.started_on) }) }}</template
          >
        </PText>
        <div class="reading-card__progress">
          <div class="reading-card__between">
            <PText as="span" tone="secondary">{{
              t('reading.shelf.pageOf', { page: book.current_page, total: book.total_pages })
            }}</PText>
            <PText variant="strong" as="span">{{ book.progress_percent }}%</PText>
          </div>
          <PProgress
            :value="book.current_page"
            :max="book.total_pages"
            tone="reading"
            :label="book.title"
          />
          <PText variant="sm" tone="muted">{{
            book.pace_pages_per_day && book.forecast_finish_on
              ? t('reading.shelf.pace', {
                  pace: decimal(Math.round(book.pace_pages_per_day), 0),
                  date: dateShort(book.forecast_finish_on),
                })
              : t('reading.shelf.noPace')
          }}</PText>
        </div>
      </div>
      <form class="reading-card__actions" @submit.prevent="submit">
        <PStepper
          v-model="page"
          prefix="p."
          :max="book.total_pages"
          :label="t('reading.page.current')"
        />
        <PButton type="submit" variant="primary" block :loading="save.isPending.value">{{
          t('reading.actions.saveProgress')
        }}</PButton>
        <PLink :to="to" :chevron="false">{{ t('reading.actions.details') }}</PLink>
      </form>
    </div>
  </PCard>
</template>

<style scoped>
.reading-card__grid {
  display: grid;
  align-items: center;
  gap: var(--space-6);
  grid-template-columns: auto minmax(0, 1fr) minmax(220px, 300px);
}

.reading-card__info {
  display: flex;
  min-width: 0;
  max-width: 780px;
  flex-direction: column;
  gap: var(--space-2);
}

.reading-card__progress {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.reading-card__between {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
}

.reading-card__actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  align-self: start;
  gap: var(--space-3);
}

@media (width < 1100px) {
  .reading-card__grid {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .reading-card__actions {
    grid-column: 1 / -1;
    align-items: stretch;
  }
}

@media (width < 600px) {
  .reading-card__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
