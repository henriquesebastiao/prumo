<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { useSessionStore } from '@/app/stores/session'
import AuthLayout from '@/layouts/AuthLayout.vue'
import { errorMessage } from '@/lib/errors'
import { PAlert, PButton, PCard, PCheckbox, PField, PInput, PNote, PText } from '@/ui'

const { t, te } = useI18n()
const router = useRouter()
const route = useRoute()
const session = useSessionStore()

const username = ref('')
const password = ref('')
const remember = ref(true)
const submitting = ref(false)
const failure = ref<string | null>(null)

async function submit() {
  if (!username.value.trim() || !password.value) return
  submitting.value = true
  failure.value = null
  try {
    await session.login({
      username: username.value,
      password: password.value,
      remember: remember.value,
    })
    const next = typeof route.query.next === 'string' ? route.query.next : '/'
    await router.replace(next.startsWith('/') ? next : '/')
  } catch (error) {
    failure.value = errorMessage(error, { t, te })
    password.value = ''
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthLayout>
    <PCard
      as="form"
      padding="lg"
      density="loose"
      class="login"
      aria-labelledby="login-title"
      novalidate
      @submit.prevent="submit"
    >
      <div class="login__heading">
        <PText id="login-title" as="h2" variant="title">{{ t('auth.login.title') }}</PText>
        <PText tone="secondary">{{ t('auth.login.subtitle') }}</PText>
      </div>
      <PAlert v-if="failure" :title="t('auth.login.failed')" :description="failure" />
      <PField :label="t('auth.login.username')">
        <PInput v-model="username" icon="user" autocomplete="username" />
      </PField>
      <PField :label="t('auth.login.password')">
        <PInput
          v-model="password"
          type="password"
          icon="lock"
          revealable
          autocomplete="current-password"
        />
      </PField>
      <PCheckbox v-model="remember">{{ t('auth.login.remember') }}</PCheckbox>
      <PButton type="submit" variant="primary" size="lg" block :loading="submitting">{{
        t('auth.login.submit')
      }}</PButton>
      <PNote>{{ t('auth.login.forgot') }}</PNote>
    </PCard>
  </AuthLayout>
</template>

<style scoped>
.login {
  width: 100%;
  max-width: 420px;
}

.login__heading {
  display: flex;
  flex-direction: column;
  gap: var(--space-0-5);
}
</style>
