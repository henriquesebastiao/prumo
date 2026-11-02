<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { useSessionStore } from '@/app/stores/session'
import { errorMessage } from '@/lib/errors'
import { apiFieldErrors, type FieldErrors } from '@/lib/forms'
import { useUpdateProfile } from '@/system/api'
import { PAlert, PAvatar, PButton, PCard, PField, PInput, useToast } from '@/ui'

import PasswordDialog from './PasswordDialog.vue'

const { t, te } = useI18n()
const session = useSessionStore()
const toast = useToast()
const update = useUpdateProfile()

const displayName = ref(session.user?.display_name ?? '')
const errors = ref<FieldErrors>({})
const failure = ref<string | null>(null)
const passwordOpen = ref(false)

watch(
  () => session.user?.display_name,
  (value) => (displayName.value = value ?? ''),
)

async function save() {
  errors.value = {}
  failure.value = null
  try {
    const user = await update.mutateAsync({ display_name: displayName.value })
    session.setUser(user)
    toast.show({ title: t('settings.profile.saved') })
  } catch (error) {
    errors.value = apiFieldErrors(error, { t, te })
    if (Object.keys(errors.value).length === 0) failure.value = errorMessage(error, { t, te })
  }
}
</script>

<template>
  <PCard as="section" :title="t('settings.profile.title')" aria-labelledby="perfil-title">
    <template #actions>
      <PButton variant="primary" :loading="update.isPending.value" @click="save">{{
        t('settings.profile.save')
      }}</PButton>
    </template>
    <PAlert v-if="failure" :title="failure" />
    <PAvatar :name="displayName || (session.user?.username ?? '')" size="lg" />
    <div class="profile__fields">
      <PField :label="t('settings.profile.name')" :error="errors.display_name">
        <PInput v-model="displayName" autocomplete="name" :maxlength="80" />
      </PField>
      <PField :label="t('settings.profile.username')" :hint="t('settings.profile.usernameHint')">
        <PInput :model-value="session.user?.username ?? ''" readonly />
      </PField>
      <PField :label="t('settings.profile.password')" label-as="span">
        <PButton icon="lock" class="profile__password" @click="passwordOpen = true">{{
          t('settings.profile.changePassword')
        }}</PButton>
      </PField>
    </div>
    <PasswordDialog v-model:open="passwordOpen" />
  </PCard>
</template>

<style scoped>
.profile__fields {
  display: grid;
  gap: var(--space-3-5) var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
}

.profile__password {
  justify-content: flex-start;
}
</style>
