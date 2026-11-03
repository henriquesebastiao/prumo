<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import {
  PAlert,
  PBookCover,
  PButton,
  PDateInput,
  PDialog,
  PField,
  PFileButton,
  PInput,
  PNumberInput,
  PSegmented,
  PSwitch,
  PText,
  useToast,
} from '@/ui'

import { coverUrl, useSaveBook, useSetCover, type Book, type BookStatus } from '../api'
import { coverVariant, STATUSES } from '../helpers'
import { today } from './today'

const props = defineProps<{ book?: Book }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveBook()
const setCover = useSetCover()

const title = ref('')
const author = ref('')
const pages = ref<number | null>(null)
const status = ref<BookStatus>('want_to_read')
const currentPage = ref<number | null>(null)
const startedOn = ref('')
const finishedOn = ref('')
const owned = ref(false)
const file = ref<File>()
const preview = ref<string>()
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)

function setPreview(value?: File) {
  if (preview.value) URL.revokeObjectURL(preview.value)
  file.value = value
  preview.value = value ? URL.createObjectURL(value) : undefined
}
onBeforeUnmount(() => setPreview())

watch(
  open,
  (value) => {
    if (!value) return
    errors.value = {}
    failure.value = null
    setPreview()
    const book = props.book
    title.value = book?.title ?? ''
    author.value = book?.author ?? ''
    pages.value = book?.total_pages ?? null
    status.value = book?.status ?? 'want_to_read'
    currentPage.value = book?.current_page ?? null
    startedOn.value = book?.started_on ?? ''
    finishedOn.value = book?.finished_on ?? ''
    owned.value = book?.owned ?? false
  },
  { immediate: true },
)
watch(status, (value) => {
  if (props.book) return
  if (value !== 'want_to_read' && !startedOn.value && value === 'reading') startedOn.value = today()
  if (value === 'read' && !finishedOn.value) finishedOn.value = today()
})

const statusOptions = computed(() =>
  STATUSES.map((value) => ({ value, label: t(`reading.status.${value}`) })),
)
const coverSource = computed(() => preview.value ?? (props.book ? coverUrl(props.book) : undefined))

function body() {
  const dates = {
    started_on: status.value === 'want_to_read' ? null : startedOn.value || null,
    finished_on: status.value === 'read' ? finishedOn.value || null : null,
  }
  const common = {
    title: title.value,
    author: author.value,
    total_pages: pages.value ?? 0,
    status: status.value,
    owned: owned.value,
  }
  if (props.book) {
    // Dates stay as they are unless the form shows them (R3, R4 fill the empty ones).
    return status.value === 'want_to_read' ? common : { ...common, ...dates }
  }
  return {
    ...common,
    ...dates,
    current_page: status.value === 'reading' ? (currentPage.value ?? 0) : 0,
  }
}

async function submit() {
  errors.value = {}
  failure.value = null
  let saved: Book
  try {
    saved = await save.mutateAsync({ id: props.book?.id, body: body() })
  } catch (error) {
    errors.value = apiFieldErrors(error, { t, te })
    if (Object.keys(errors.value).length === 0) failure.value = errorMessage(error, { t, te })
    return
  }
  if (file.value) {
    try {
      await setCover.mutateAsync({ id: saved.id, file: file.value })
    } catch (error) {
      toast.show({
        title: t('reading.form.coverFailed', { reason: errorMessage(error, { t, te }) }),
        tone: 'danger',
      })
    }
  }
  toast.show({ title: t('reading.form.saved') })
  open.value = false
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="book ? t('reading.form.editTitle') : t('reading.form.newTitle')"
    icon="book"
    tone="reading"
    size="l"
  >
    <form id="book-form" class="form__split" novalidate @submit.prevent="submit">
      <div class="form__cover">
        <PField :label="t('reading.form.cover')" optional label-as="span">
          <PBookCover
            :title="title || t('reading.form.title')"
            :author="author"
            :src="coverSource"
            :variant="coverVariant(status)"
            size="xl"
          />
        </PField>
        <PFileButton accept="image/jpeg,image/png,image/webp" block @select="setPreview">{{
          t('reading.form.upload')
        }}</PFileButton>
        <PText variant="sm" tone="muted">{{ t('reading.form.coverHint') }}</PText>
      </div>
      <div class="form">
        <PAlert v-if="failure" :title="failure" />
        <PField :label="t('reading.form.title')" :error="errors.title">
          <PInput v-model="title" :maxlength="200" />
        </PField>
        <PField :label="t('reading.form.author')" :error="errors.author">
          <PInput v-model="author" :maxlength="120" />
        </PField>
        <div class="form__pages">
          <PField :label="t('reading.form.pages')" :error="errors.total_pages">
            <PNumberInput v-model="pages" :suffix="t('reading.form.pagesSuffix')" />
          </PField>
        </div>
        <PField
          :label="t('reading.form.status')"
          label-as="span"
          :hint="t('reading.form.statusHint')"
        >
          <PSegmented
            v-model="status"
            :options="statusOptions"
            :label="t('reading.form.status')"
            block
          />
        </PField>
        <div v-if="status !== 'want_to_read'" class="form__row">
          <PField
            v-if="status === 'reading' && !book"
            :label="t('reading.form.currentPage')"
            :error="errors.current_page"
          >
            <PNumberInput v-model="currentPage" prefix="p." />
          </PField>
          <PField :label="t('reading.form.startedOn')" :error="errors.started_on" optional>
            <PDateInput v-model="startedOn" />
          </PField>
          <PField
            v-if="status === 'read'"
            :label="t('reading.form.finishedOn')"
            :error="errors.finished_on"
          >
            <PDateInput v-model="finishedOn" />
          </PField>
        </div>
        <div class="form__switch">
          <span class="form__switch-text">
            <PText variant="h3" as="span">{{ t('reading.form.owned') }}</PText>
            <PText variant="sm" tone="muted" as="span">{{ t('reading.form.ownedHint') }}</PText>
          </span>
          <PSwitch v-model="owned" :label="t('reading.form.owned')" />
        </div>
      </div>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="book-form"
        variant="primary"
        :loading="save.isPending.value || setCover.isPending.value"
        >{{ book ? t('reading.actions.save') : t('reading.form.create') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
