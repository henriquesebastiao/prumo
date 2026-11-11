<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { dateShort } from '@/lib/format'
import {
  PBadge,
  PButton,
  PCard,
  PEmptyState,
  PIconButton,
  PList,
  PListItem,
  PMenu,
  PQueryState,
  PText,
  PTile,
  useToast,
  type MenuEntry,
} from '@/ui'

import {
  useArchiveArea,
  useArchiveSubject,
  useAreas,
  useDeleteArea,
  useSubjects,
  type Area,
  type Subject,
} from '../api'
import AreaDialog from '../forms/AreaDialog.vue'
import SubjectDialog from '../forms/SubjectDialog.vue'
import { colorTone, minutes } from '../helpers'

const { t, te } = useI18n()
const toast = useToast()
const showArchived = ref(false)
const archivedParam = computed(() => (showArchived.value ? 'all' : 'false') as 'all' | 'false')
const areas = useAreas(archivedParam)
const subjects = useSubjects(() => ({ archived: archivedParam.value }))
const archiveArea = useArchiveArea()
const archiveSubject = useArchiveSubject()
const deleteArea = useDeleteArea()

const areaOpen = ref(false)
const editingArea = ref<Area>()
const subjectOpen = ref(false)
const editingSubject = ref<Subject>()
const newSubjectArea = ref<string>()

const byArea = computed(() => {
  const map = new Map<string, Subject[]>()
  for (const subject of subjects.data.value ?? []) {
    map.set(subject.area_id, [...(map.get(subject.area_id) ?? []), subject])
  }
  return map
})

async function run(action: () => Promise<unknown>, success?: string) {
  try {
    await action()
    if (success) toast.show({ title: success })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  }
}

function openArea(area?: Area) {
  editingArea.value = area
  areaOpen.value = true
}
function openSubject(areaId?: string, subject?: Subject) {
  editingSubject.value = subject
  newSubjectArea.value = areaId
  subjectOpen.value = true
}

function areaMenu(area: Area): MenuEntry[] {
  const archived = area.archived_at !== null
  return [
    { label: t('studies.actions.newSubject'), icon: 'add', onSelect: () => openSubject(area.id) },
    { label: t('studies.actions.edit'), icon: 'edit', onSelect: () => openArea(area) },
    {
      label: t(archived ? 'studies.actions.unarchive' : 'studies.actions.archive'),
      icon: 'archive',
      onSelect: () => run(() => archiveArea.mutateAsync({ id: area.id, archived: !archived })),
    },
    ...(area.subjects_count === 0
      ? [
          { type: 'separator' as const },
          {
            label: t('studies.actions.delete'),
            icon: 'trash' as const,
            tone: 'danger' as const,
            onSelect: () => run(() => deleteArea.mutateAsync(area.id)),
          },
        ]
      : []),
  ]
}

function subjectMenu(subject: Subject): MenuEntry[] {
  const archived = subject.archived_at !== null
  return [
    {
      label: t('studies.actions.edit'),
      icon: 'edit',
      onSelect: () => openSubject(undefined, subject),
    },
    {
      label: t(archived ? 'studies.actions.unarchive' : 'studies.actions.archive'),
      icon: 'archive',
      onSelect: () =>
        run(() => archiveSubject.mutateAsync({ id: subject.id, archived: !archived })),
    },
  ]
}

function subtitle(subject: Subject): string {
  const parts = [t('studies.subjects.topics', subject.topics_count)]
  if (subject.minutes_this_week) {
    parts.push(t('studies.subjects.thisWeek', { minutes: minutes(subject.minutes_this_week) }))
  } else if (subject.last_session_at) {
    parts.push(t('studies.subjects.lastSession', { date: dateShort(subject.last_session_at) }))
  } else {
    parts.push(t('studies.subjects.noSessions'))
  }
  return parts.join(' · ')
}
</script>

<template>
  <PQueryState
    :loading="areas.isPending.value || subjects.isPending.value"
    :error="areas.error.value ?? subjects.error.value"
    :error-title="t('ui.loadFailed')"
  >
    <div class="subjects">
      <div class="subjects__toolbar">
        <PButton variant="ghost" @click="showArchived = !showArchived">{{
          t(showArchived ? 'studies.actions.hideArchived' : 'studies.actions.showArchived')
        }}</PButton>
        <PButton variant="outline" icon="add" @click="openArea()">{{
          t('studies.actions.newArea')
        }}</PButton>
      </div>
      <PEmptyState
        v-if="!areas.data.value?.length"
        :title="t('studies.subjects.empty')"
        :description="t('studies.subjects.emptyHint')"
        icon="graduation-cap"
        tone="studies"
        variant="card"
      />
      <PCard
        v-for="area in areas.data.value"
        :key="area.id"
        as="section"
        :title="area.name"
        :subtitle="t('studies.subjects.count', area.subjects_count)"
        icon="graduation-cap"
        :tone="colorTone(area.color)"
      >
        <template #actions>
          <PBadge v-if="area.archived_at" variant="outline">{{
            t('studies.subjects.archived')
          }}</PBadge>
          <PMenu :items="areaMenu(area)">
            <template #trigger>
              <PIconButton icon="more" :label="t('studies.actions.more')" variant="ghost" />
            </template>
          </PMenu>
        </template>
        <PList v-if="byArea.get(area.id)?.length">
          <PListItem
            v-for="subject in byArea.get(area.id)"
            :key="subject.id"
            :title="subject.name"
            :subtitle="subtitle(subject)"
            :to="{ name: 'studies.subject', params: { subjectId: subject.id } }"
          >
            <template #leading>
              <PTile icon="book-open" :tone="colorTone(subject.color)" />
            </template>
            <template #trailing>
              <PBadge v-if="subject.archived_at" variant="outline">{{
                t('studies.subjects.archived')
              }}</PBadge>
              <PMenu :items="subjectMenu(subject)">
                <template #trigger>
                  <PIconButton
                    icon="more"
                    :label="t('studies.actions.more')"
                    variant="ghost"
                    size="sm"
                  />
                </template>
              </PMenu>
            </template>
          </PListItem>
        </PList>
        <PText v-else tone="secondary">{{ t('studies.subjects.noSubjects') }}</PText>
      </PCard>
    </div>
  </PQueryState>
  <AreaDialog v-model:open="areaOpen" :area="editingArea" />
  <SubjectDialog v-model:open="subjectOpen" :subject="editingSubject" :area-id="newSubjectArea" />
</template>

<style scoped>
.subjects {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.subjects__toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-2);
}
</style>
