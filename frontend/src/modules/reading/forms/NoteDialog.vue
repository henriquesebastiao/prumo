<script setup lang="ts">
/** New or edited note; without a book (quick action) it asks which one. */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import {
  PAlert,
  PButton,
  PDateInput,
  PDialog,
  PField,
  PKbd,
  PNumberInput,
  PSelect,
  PText,
  PTextarea,
  useToast,
} from '@/ui'

import { useBooks, useSaveNote, type Book, type Note } from '../api'
import { today } from './today'

const props = defineProps<{ book?: Book; note?: Note }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveNote()
const books = useBooks()

const bookId = ref('')
const content = ref('')
const page = ref<number | null>(null)
const day = ref('')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)

/** Books for the quick action: being read first, then the others. */
const choices = computed(() => {
  const order = { reading: 0, want_to_read: 1, read: 2 } as const
  return [...(books.data.value ?? [])].sort(
    (a, b) =>
      order[a.status] - order[b.status] ||
      (b.last_progress_at ?? b.created_at).localeCompare(a.last_progress_at ?? a.created_at),
  )
})
const selected = computed(() => props.book ?? choices.value.find((b) => b.id === bookId.value))
const bookOptions = computed(() => choices.value.map((b) => ({ value: b.id, label: b.title })))

function reset() {
  errors.value = {}
  failure.value = null
  bookId.value = props.book?.id ?? choices.value[0]?.id ?? ''
  content.value = props.note?.content ?? ''
  page.value = props.note ? props.note.page : (selected.value?.current_page ?? null) || null
  day.value = props.note?.noted_on ?? today()
}
watch(open, (value) => value && reset(), { immediate: true })
watch(choices, () => {
  if (!bookId.value && open.value && !props.note) reset()
})
watch(bookId, () => {
  if (!props.note && !props.book) page.value = selected.value?.current_page || null
})

async function submit() {
  const book = selected.value
  if (!book) return
  errors.value = {}
  failure.value = null
  try {
    await save.mutateAsync({
      bookId: book.id,
      id: props.note?.id,
      body: { content: content.value, page: page.value, noted_on: day.value || null },
    })
    toast.show({ title: t('reading.note.saved') })
    open.value = false
  } catch (error) {
    errors.value = apiFieldErrors(error, { t, te })
    if (Object.keys(errors.value).length === 0) failure.value = errorMessage(error, { t, te })
  }
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault()
    void submit()
  }
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="note ? t('reading.note.editTitle') : t('reading.note.newTitle')"
    :description="
      selected ? t('reading.note.subtitle', { title: selected.title, author: selected.author }) : ''
    "
    icon="note"
    tone="reading"
  >
    <form id="note-form" class="form" novalidate @submit.prevent="submit" @keydown="onKeydown">
      <PText v-if="books.isSuccess.value && !choices.length && !book" tone="secondary">{{
        t('reading.note.noBooks')
      }}</PText>
      <PField v-if="!book && !note && choices.length > 1" :label="t('reading.note.book')">
        <PSelect v-model="bookId" :options="bookOptions" />
      </PField>
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('reading.note.content')" :error="errors.content" data-autofocus>
        <PTextarea v-model="content" :rows="6" />
      </PField>
      <div class="form__row">
        <PField
          :label="t('reading.note.page')"
          optional
          :hint="note ? undefined : t('reading.note.pageHint')"
          :error="errors.page"
        >
          <PNumberInput v-model="page" prefix="p." />
        </PField>
        <PField :label="t('reading.note.date')" :error="errors.noted_on">
          <PDateInput v-model="day" />
        </PField>
      </div>
    </form>
    <template #footer>
      <span class="form__footer-start">
        <PKbd>{{ t('reading.note.keyCtrl') }}</PKbd>
        <PText variant="sm" tone="muted" as="span">+</PText>
        <PKbd>{{ t('reading.note.keyEnter') }}</PKbd>
        <PText variant="sm" tone="muted" as="span">{{ t('reading.note.shortcut') }}</PText>
      </span>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="note-form"
        variant="primary"
        :loading="save.isPending.value"
        :disabled="!selected"
        >{{ t('reading.note.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
