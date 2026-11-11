<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { errorMessage } from '@/lib/errors'
import { dateShort, relativeDateTime } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PChart,
  PConfirmDialog,
  PIconButton,
  PLink,
  PList,
  PListItem,
  PMenu,
  PPageHeader,
  PQueryState,
  PStatCard,
  PText,
  useToast,
  type MenuEntry,
} from '@/ui'

import {
  useArchiveSubject,
  useDeleteSession,
  useDeleteSubject,
  useDeleteTopic,
  useSubject,
  type StudySession,
} from '../api'
import SessionDialog from '../forms/SessionDialog.vue'
import SubjectDialog from '../forms/SubjectDialog.vue'
import { minutes } from '../helpers'

const props = defineProps<{ subjectId: string }>()
const { t, te } = useI18n()
const toast = useToast()
const router = useRouter()
const query = useSubject(() => props.subjectId)
const subject = computed(() => query.data.value)
const archive = useArchiveSubject()
const remove = useDeleteSubject()
const removeSession = useDeleteSession()
const removeTopic = useDeleteTopic()

const editing = ref(false)
const confirming = ref(false)
const sessionOpen = ref(false)
const editingSession = ref<StudySession>()

async function run(action: () => Promise<unknown>, success?: string) {
  try {
    await action()
    if (success) toast.show({ title: success })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}

const menu = computed<MenuEntry[]>(() => {
  const archived = subject.value?.archived_at !== null
  return [
    { label: t('studies.actions.edit'), icon: 'edit', onSelect: () => (editing.value = true) },
    {
      label: t(archived ? 'studies.actions.unarchive' : 'studies.actions.archive'),
      icon: 'archive',
      onSelect: () => run(() => archive.mutateAsync({ id: props.subjectId, archived: !archived })),
    },
    { type: 'separator' },
    {
      label: t('studies.actions.delete'),
      icon: 'trash',
      tone: 'danger',
      onSelect: () => (confirming.value = true),
    },
  ]
})

async function destroy() {
  await run(() => remove.mutateAsync(props.subjectId), t('studies.subject.deleted'))
  confirming.value = false
  await router.push({ name: 'studies.subjects' })
}

function openSession(session?: StudySession) {
  editingSession.value = session
  sessionOpen.value = true
}

const weekly = computed(() =>
  (subject.value?.weekly_minutes ?? []).map((week) => ({
    label: dateShort(week.week_start),
    value: week.minutes,
  })),
)
const hasWeekly = computed(() => weekly.value.some((week) => week.value > 0))
</script>

<template>
  <PQueryState
    :loading="query.isPending.value"
    :error="query.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <div v-if="subject" class="subject">
      <PPageHeader
        :overline="subject.area_name"
        :title="subject.name"
        :back="{ label: t('studies.subject.back'), to: { name: 'studies.subjects' } }"
      >
        <PBadge v-if="subject.archived_at" variant="outline">{{
          t('studies.subjects.archived')
        }}</PBadge>
        <PButton variant="primary" icon="add" @click="openSession()">{{
          t('studies.actions.logSession')
        }}</PButton>
        <PMenu :items="menu">
          <template #trigger>
            <PIconButton icon="more" :label="t('studies.actions.more')" />
          </template>
        </PMenu>
      </PPageHeader>

      <div class="subject__stats">
        <PStatCard
          :label="t('studies.subject.thisWeek')"
          :value="minutes(subject.minutes_this_week)"
        />
        <PStatCard
          :label="t('studies.subject.lastSession')"
          :value="subject.last_session_at ? relativeDateTime(subject.last_session_at) : '—'"
        />
        <PCard as="section" variant="flat" padding="sm">
          <PLink v-if="subject.obsidian_uri" :href="subject.obsidian_uri">{{
            t('studies.actions.openObsidian')
          }}</PLink>
          <PText v-else tone="secondary" variant="sm">{{
            t('studies.subject.obsidianMissing')
          }}</PText>
        </PCard>
      </div>

      <PCard as="section" :title="t('studies.subject.weekly')">
        <PChart
          v-if="hasWeekly"
          type="bars"
          :data="weekly"
          tone="studies"
          :label="t('studies.subject.weekly')"
          :format="minutes"
        />
        <PText v-else tone="secondary">{{ t('studies.subject.weeklyEmpty') }}</PText>
      </PCard>

      <PCard as="section" :title="t('studies.subject.topics')">
        <div v-if="subject.topics.length" class="subject__topics">
          <PBadge
            v-for="topic in subject.topics"
            :key="topic.id"
            variant="tag"
            :icon="topic.sessions_count ? undefined : 'close'"
          >
            {{ topic.name }} · {{ t('studies.subject.sessionsCount', topic.sessions_count) }}
            <button
              v-if="!topic.sessions_count"
              type="button"
              class="subject__remove"
              :aria-label="t('studies.actions.deleteTopic')"
              @click="run(() => removeTopic.mutateAsync(topic.id))"
            >
              ×
            </button>
          </PBadge>
        </div>
        <PText v-else tone="secondary">{{ t('studies.subject.noTopics') }}</PText>
      </PCard>

      <PCard as="section" :title="t('studies.subject.recent')">
        <PList v-if="subject.recent_sessions.length">
          <PListItem
            v-for="session in subject.recent_sessions"
            :key="session.id"
            :title="minutes(session.duration_minutes)"
            :subtitle="
              [relativeDateTime(session.started_at), session.topic?.name]
                .filter(Boolean)
                .join(' · ')
            "
          >
            <template #trailing>
              <PIconButton
                icon="edit"
                :label="t('studies.actions.editSession')"
                variant="ghost"
                size="sm"
                @click="openSession(session)"
              />
              <PIconButton
                icon="trash"
                :label="t('studies.actions.deleteSession')"
                variant="ghost"
                size="sm"
                @click="run(() => removeSession.mutateAsync(session.id))"
              />
            </template>
          </PListItem>
        </PList>
        <PText v-else tone="secondary">{{ t('studies.subject.noRecent') }}</PText>
      </PCard>
    </div>
  </PQueryState>
  <SubjectDialog v-model:open="editing" :subject="subject" />
  <SessionDialog v-model:open="sessionOpen" :subject-id="subjectId" :session="editingSession" />
  <PConfirmDialog
    v-model:open="confirming"
    :title="t('studies.subject.deleteTitle')"
    :description="t('studies.subject.deleteBody', { name: subject?.name ?? '' })"
    :confirm-label="t('studies.actions.delete')"
    tone="danger"
    icon="trash"
    :loading="remove.isPending.value"
    @confirm="destroy"
  />
</template>

<style scoped>
.subject {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.subject__stats {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
}

.subject__topics {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.subject__remove {
  margin-left: var(--space-1);
  border: 0;
  background: none;
  color: inherit;
  cursor: pointer;
}
</style>
