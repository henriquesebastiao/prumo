<script setup lang="ts">
/** New or edited area: name and color. */
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import { PAlert, PButton, PDialog, PField, PInput, PSwatchPicker, useToast } from '@/ui'

import { useSaveArea, type Area } from '../api'
import { swatchOptions, type StudiesColor } from '../helpers'

const props = defineProps<{ area?: Area }>()
const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const save = useSaveArea()

const name = ref('')
const color = ref<StudiesColor>('blue')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)

watch(
  open,
  (value) => {
    if (!value) return
    errors.value = {}
    failure.value = null
    name.value = props.area?.name ?? ''
    color.value = (props.area?.color as StudiesColor | undefined) ?? 'blue'
  },
  { immediate: true },
)

async function submit() {
  errors.value = {}
  failure.value = null
  try {
    await save.mutateAsync({
      id: props.area?.id,
      body: { name: name.value.trim(), color: color.value },
    })
    toast.show({ title: t('studies.form.saved.area') })
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
    :title="t(area ? 'studies.form.titles.editArea' : 'studies.form.titles.newArea')"
    icon="graduation-cap"
    tone="studies"
    size="s"
  >
    <form id="area-form" class="form" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('studies.form.name')" :error="errors.name">
        <PInput v-model="name" />
      </PField>
      <PField :label="t('studies.form.color')" label-as="span" :error="errors.color">
        <PSwatchPicker
          v-model="color"
          :options="swatchOptions(t, area?.color)"
          :label="t('studies.form.color')"
        />
      </PField>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="area-form"
        variant="primary"
        :loading="save.isPending.value"
        :disabled="!name.trim()"
        >{{ t('studies.actions.save') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style src="./form.css" scoped></style>
