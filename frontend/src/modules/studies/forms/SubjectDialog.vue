<script setup lang="ts">
/** New or edited subject: area, name and the Obsidian link (E8). */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import { PAlert, PButton, PDialog, PField, PInput, PSelect, useToast } from '@/ui'

import { useAreas, useSaveSubject, type Subject } from '../api'

const props = defineProps<{ subject?: Subject; areaId?: string }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const saveSubject = useSaveSubject()
// Exposed as its own ref: vue-tsc loses the mutation's type in this template otherwise.
const saving = saveSubject.isPending
const areas = useAreas()

const chosenArea = ref('')
const name = ref('')
const uri = ref('')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)

const areaOptions = computed(() =>
  (areas.data.value ?? []).map((area) => ({ value: area.id, label: area.name })),
)

watch(
  open,
  (value) => {
    if (!value) return
    errors.value = {}
    failure.value = null
    chosenArea.value = props.subject?.area_id ?? props.areaId ?? areas.data.value?.[0]?.id ?? ''
    name.value = props.subject?.name ?? ''
    uri.value = props.subject?.obsidian_uri ?? ''
  },
  { immediate: true },
)
watch(areaOptions, (options) => {
  if (!chosenArea.value && options[0]) chosenArea.value = options[0].value
})

async function submit() {
  errors.value = {}
  failure.value = null
  const trimmed = uri.value.trim()
  try {
    await saveSubject.mutateAsync({
      id: props.subject?.id,
      body: {
        area_id: chosenArea.value,
        name: name.value.trim(),
        obsidian_uri: trimmed || null,
      },
    })
    toast.show({ title: t('studies.form.saved.subject') })
    open.value = false
  } catch (error) {
    errors.value = apiFieldErrors(error, { t, te })
    if (!Object.keys(errors.value).length) failure.value = errorMessage(error, { t, te })
  }
}
</script>

<template>
  <PDialog
    v-model:open="open"
    :title="t(subject ? 'studies.form.titles.editSubject' : 'studies.form.titles.newSubject')"
    icon="book-open"
    tone="studies"
    size="s"
  >
    <form id="subject-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('studies.form.area')" :error="errors.area_id">
        <PSelect v-model="chosenArea" :options="areaOptions" />
      </PField>
      <PField :label="t('studies.form.name')" :error="errors.name">
        <PInput v-model="name" />
      </PField>
      <PField
        :label="t('studies.form.obsidian')"
        :hint="t('studies.form.obsidianHint')"
        :error="errors.obsidian_uri"
        optional
      >
        <PInput v-model="uri" type="url" placeholder="obsidian://open?vault=…" />
      </PField>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="subject-form"
        variant="primary"
        :loading="saving"
        :disabled="!name.trim() || !chosenArea"
        >{{ t('studies.actions.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
