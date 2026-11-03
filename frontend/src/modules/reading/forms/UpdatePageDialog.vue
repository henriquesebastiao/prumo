<script setup lang="ts">
/** Quick action "Atualizar página": the current page of a book being read. */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { PAlert, PButton, PDialog, PField, PSelect, PStepper, PText, useToast } from '@/ui'

import { useBooks, useSaveProgress } from '../api'

const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveProgress()
const books = useBooks({ status: 'reading' })

const reading = computed(() =>
  [...(books.data.value ?? [])].sort((a, b) =>
    (b.last_progress_at ?? b.created_at).localeCompare(a.last_progress_at ?? a.created_at),
  ),
)
const bookId = ref('')
const page = ref(0)
const failure = ref<string | null>(null)
const selected = computed(() => reading.value.find((book) => book.id === bookId.value))

function pick() {
  failure.value = null
  bookId.value = reading.value[0]?.id ?? ''
}
watch(open, (value) => value && pick(), { immediate: true })
watch(reading, () => {
  if (!selected.value) pick()
})
watch(selected, (book) => (page.value = book?.current_page ?? 0), { immediate: true })

const options = computed(() => reading.value.map((book) => ({ value: book.id, label: book.title })))

async function submit() {
  if (!selected.value) return
  try {
    await save.mutateAsync({ id: selected.value.id, page: page.value })
    toast.show({ title: t('reading.shelf.pageSaved') })
    open.value = false
  } catch (error) {
    failure.value = errorMessage(error, { t, te })
  }
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t('reading.page.title')"
    icon="bookmark"
    tone="reading"
    size="s"
  >
    <form id="page-form" class="form" novalidate @submit.prevent="submit">
      <PText v-if="books.isSuccess.value && !reading.length" tone="secondary">{{
        t('reading.page.noBooks')
      }}</PText>
      <PAlert v-if="failure" :title="failure" />
      <PField v-if="reading.length > 1" :label="t('reading.page.book')">
        <PSelect v-model="bookId" :options="options" />
      </PField>
      <PField v-if="selected" :label="t('reading.page.current')" label-as="span">
        <div class="form__stepper">
          <PStepper
            v-model="page"
            prefix="p."
            :max="selected.total_pages"
            :label="t('reading.page.current')"
          />
          <PText tone="muted" as="span">{{
            t('reading.page.of', { total: selected.total_pages })
          }}</PText>
        </div>
      </PField>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="page-form"
        variant="primary"
        :loading="save.isPending.value"
        :disabled="!selected"
        >{{ t('reading.actions.saveProgress') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
