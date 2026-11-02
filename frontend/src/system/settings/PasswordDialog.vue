<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { z } from 'zod'

import { isApiError } from '@/lib/api/errors'
import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, zodFieldErrors, type FieldErrors } from '@/lib/forms'
import { useChangePassword } from '@/system/api'
import { PAlert, PButton, PDialog, PField, PInput, useToast } from '@/ui'

const open = defineModel<boolean>('open', { default: false })
const { t, te } = useI18n()
const toast = useToast()
const change = useChangePassword()

const current = ref('')
const next = ref('')
const confirm = ref('')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)

watch(open, (value) => {
  if (!value) return
  current.value = next.value = confirm.value = ''
  errors.value = {}
  failure.value = null
})

function schema() {
  return z
    .object({
      current_password: z.string().min(1, t('fieldErrors.missing')),
      new_password: z.string().min(8, t('errors.users.password_too_short', { min_length: 8 })),
      confirm: z.string(),
    })
    .refine((data) => data.new_password === data.confirm, {
      path: ['confirm'],
      message: t('settings.password.mismatch'),
    })
}

async function submit() {
  failure.value = null
  const parsed = schema().safeParse({
    current_password: current.value,
    new_password: next.value,
    confirm: confirm.value,
  })
  if (!parsed.success) {
    errors.value = zodFieldErrors(parsed.error)
    return
  }
  errors.value = {}
  try {
    await change.mutateAsync({ current_password: current.value, new_password: next.value })
    open.value = false
    toast.show({ title: t('settings.password.changed') })
  } catch (error) {
    if (isApiError(error) && error.code === 'auth.wrong_password') {
      errors.value = { current_password: errorMessage(error, { t, te }) }
      return
    }
    errors.value = apiFieldErrors(error, { t, te })
    if (Object.keys(errors.value).length === 0) failure.value = errorMessage(error, { t, te })
  }
}
</script>

<template>
  <PDialog v-model:open="open" :title="t('settings.password.title')" size="s">
    <form id="password-form" class="password" novalidate @submit.prevent="submit">
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('settings.password.current')" :error="errors.current_password">
        <PInput v-model="current" type="password" revealable autocomplete="current-password" />
      </PField>
      <PField
        :label="t('settings.password.new')"
        :hint="t('settings.password.hint')"
        :error="errors.new_password"
      >
        <PInput v-model="next" type="password" revealable autocomplete="new-password" />
      </PField>
      <PField :label="t('settings.password.confirm')" :error="errors.confirm">
        <PInput v-model="confirm" type="password" revealable autocomplete="new-password" />
      </PField>
    </form>
    <template #footer>
      <PButton @click="open = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="password-form"
        variant="primary"
        :loading="change.isPending.value"
        >{{ t('settings.password.submit') }}</PButton
      >
    </template>
  </PDialog>
</template>

<style scoped>
.password {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
</style>
