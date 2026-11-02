<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/lib/api/client'
import { errorMessage } from '@/lib/errors'
import { date, relativeDateTime } from '@/lib/format'
import { useRevokeSession, useSessions } from '@/system/api'
import {
  PBadge,
  PButton,
  PCard,
  PConfirmDialog,
  PList,
  PListItem,
  PQueryState,
  PText,
  PTile,
  useToast,
} from '@/ui'

type Session = Schemas['SessionRead']

const { t, te } = useI18n()
const toast = useToast()
const sessions = useSessions()
const revoke = useRevokeSession()
const target = ref<Session | null>(null)
const confirmOpen = computed({
  get: () => target.value !== null,
  set: (open: boolean) => {
    if (!open) target.value = null
  },
})

function deviceName(session: Session): string {
  return session.device_name ?? t('settings.sessions.unknownDevice')
}

function details(session: Session): string {
  return [
    t(`settings.sessions.${session.client}`),
    t('settings.sessions.lastUsed', { when: relativeDateTime(session.last_used_at) }),
    t('settings.sessions.expires', { date: date(session.expires_at) }),
  ].join(' · ')
}

async function confirmRevoke() {
  if (!target.value) return
  try {
    await revoke.mutateAsync(target.value.id)
    toast.show({ title: t('settings.sessions.ended') })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  } finally {
    target.value = null
  }
}
</script>

<template>
  <PCard as="section">
    <template #header>
      <div class="sessions__heading">
        <PText as="h2" variant="h2">{{ t('settings.sessions.title') }}</PText>
        <PText variant="sm" tone="muted">{{ t('settings.sessions.description') }}</PText>
      </div>
    </template>
    <PQueryState
      :loading="sessions.isPending.value"
      :error="sessions.error.value"
      :error-title="t('settings.sessions.loadFailed')"
      @retry="sessions.refetch()"
    >
      <PList>
        <PListItem
          v-for="session in sessions.data.value ?? []"
          :key="session.id"
          :title="deviceName(session)"
          :subtitle="details(session)"
        >
          <template #leading>
            <PTile :icon="session.client === 'app' ? 'smartphone' : 'monitor'" />
          </template>
          <template #trailing>
            <PBadge v-if="session.current" variant="solid">{{
              t('settings.sessions.current')
            }}</PBadge>
            <PButton v-else variant="ghost" @click="target = session">{{
              t('settings.sessions.end')
            }}</PButton>
          </template>
        </PListItem>
      </PList>
    </PQueryState>
    <PConfirmDialog
      v-model:open="confirmOpen"
      :title="t('settings.sessions.confirmTitle')"
      :description="
        t('settings.sessions.confirmDescription', { device: target ? deviceName(target) : '' })
      "
      :confirm-label="t('settings.sessions.end')"
      icon="logout"
      :loading="revoke.isPending.value"
      @confirm="confirmRevoke"
    />
  </PCard>
</template>

<style scoped>
.sessions__heading {
  display: flex;
  flex-direction: column;
  gap: var(--space-0-5);
}
</style>
