<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { errorMessage } from '@/lib/errors'
import { date } from '@/lib/format'
import {
  PButton,
  PCard,
  PConfirmDialog,
  PDialog,
  PEmptyState,
  PField,
  PIconButton,
  PInput,
  PList,
  PListItem,
  PQueryState,
  PTextarea,
  PTile,
  useToast,
} from '@/ui'

import { useDeleteWorkshop, useSaveWorkshop, useWorkshops, type Workshop } from '../api'
import { useFormErrors } from '../forms/useGarageForm'

const { t, te } = useI18n()
const toast = useToast()
const workshops = useWorkshops()
const save = useSaveWorkshop()
const remove = useDeleteWorkshop()
const { errors, failure, capture, clear } = useFormErrors()

const editing = ref<Workshop | null>(null)
const formOpen = ref(false)
const name = ref('')
const notes = ref('')
const deleting = ref<Workshop | null>(null)

function edit(workshop: Workshop | null) {
  clear()
  editing.value = workshop
  name.value = workshop?.name ?? ''
  notes.value = workshop?.notes ?? ''
  formOpen.value = true
}

async function submit() {
  try {
    await save.mutateAsync({
      id: editing.value?.id,
      body: { name: name.value, notes: notes.value.trim() || null },
    })
    formOpen.value = false
    toast.show({ title: t('garage.workshops.saved') })
  } catch (error) {
    capture(error, 'name')
  }
}

async function destroy() {
  if (!deleting.value) return
  try {
    await remove.mutateAsync(deleting.value.id)
    toast.show({ title: t('garage.workshops.deleted') })
  } catch (error) {
    toast.show({ title: errorMessage(error, { t, te }), tone: 'danger' })
  } finally {
    deleting.value = null
  }
}

function stats(workshop: Workshop): string {
  return t(
    'garage.workshops.stats',
    { date: workshop.last_maintenance_at ? date(workshop.last_maintenance_at) : '' },
    workshop.maintenances_count,
  )
}

const deleteOpen = computed({
  get: () => deleting.value !== null,
  set: (v) => !v && (deleting.value = null),
})
</script>

<template>
  <PCard :title="t('garage.workshops.title')">
    <template #actions>
      <PButton icon="add" @click="edit(null)">{{ t('garage.workshops.new') }}</PButton>
    </template>
    <PQueryState
      :loading="workshops.isPending.value"
      :error="workshops.error.value"
      :empty="(workshops.data.value ?? []).length === 0"
      @retry="workshops.refetch()"
    >
      <template #empty>
        <PEmptyState
          icon="wrench"
          tone="garage"
          :description="t('garage.workshops.empty')"
          :title="t('garage.workshops.title')"
        />
      </template>
      <PList>
        <PListItem
          v-for="workshop in workshops.data.value"
          :key="workshop.id"
          :title="workshop.name"
          :subtitle="stats(workshop)"
        >
          <template #leading><PTile icon="wrench" tone="garage" shape="circle" /></template>
          <template #trailing>
            <PIconButton icon="edit" :label="t('garage.workshops.edit')" @click="edit(workshop)" />
            <PIconButton
              icon="trash"
              :label="t('garage.actions.delete')"
              @click="deleting = workshop"
            />
          </template>
        </PListItem>
      </PList>
    </PQueryState>
  </PCard>

  <PDialog
    v-model:open="formOpen"
    :title="t(editing ? 'garage.workshops.edit' : 'garage.workshops.new')"
    icon="wrench"
    tone="garage"
    size="s"
  >
    <form id="workshop-form" class="workshop-form" novalidate @submit.prevent="submit">
      <PField :label="t('garage.workshops.name')" :error="errors.name ?? failure ?? undefined">
        <PInput v-model="name" :maxlength="80" />
      </PField>
      <PField :label="t('garage.workshops.notes')" optional>
        <PTextarea v-model="notes" :rows="3" />
      </PField>
    </form>
    <template #footer>
      <PButton @click="formOpen = false">{{ t('ui.cancel') }}</PButton>
      <PButton
        type="submit"
        form="workshop-form"
        variant="primary"
        :loading="save.isPending.value"
        >{{ t('ui.save') }}</PButton
      >
    </template>
  </PDialog>
  <PConfirmDialog
    v-model:open="deleteOpen"
    :title="t('garage.workshops.deleteTitle')"
    :description="t('garage.workshops.deleteDescription', { name: deleting?.name ?? '' })"
    :confirm-label="t('garage.actions.delete')"
    :loading="remove.isPending.value"
    @confirm="destroy"
  />
</template>

<style scoped>
.workshop-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
</style>
