<script setup lang="ts">
/** Side panel of the Categorias tab: creates or edits a category (F8: used ones are archived). */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  PAlert,
  PButton,
  PCard,
  PConfirmDialog,
  PField,
  PIconButton,
  PIconPicker,
  PInput,
  PPanel,
  PSegmented,
  PSwatchPicker,
  PText,
  PTile,
  useToast,
} from '@/ui'

import {
  useArchiveCategory,
  useDeleteCategory,
  useSaveCategory,
  type Category,
  type CategoryKind,
} from '../api'
import {
  CATEGORY_ICONS,
  colorTone,
  dataIcon,
  iconOptions,
  swatchOptions,
  type FinanceColor,
} from '../helpers'
import { useFormErrors } from './useFinanceForm'

const props = defineProps<{ category?: Category; kind?: CategoryKind }>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()
const toast = useToast()
const save = useSaveCategory()
const archive = useArchiveCategory()
const remove = useDeleteCategory()
const { errors, failure, capture, clear } = useFormErrors()

const name = ref('')
const categoryKind = ref<CategoryKind>('expense')
const icon = ref('tag')
const color = ref<FinanceColor>('gray')
const confirmOpen = ref(false)

function reset() {
  clear()
  name.value = props.category?.name ?? ''
  categoryKind.value = props.category?.kind ?? props.kind ?? 'expense'
  icon.value = props.category?.icon ?? 'tag'
  color.value = (props.category?.color as FinanceColor | undefined) ?? 'gray'
}
watch(() => props.category, reset, { immediate: true })

const initialColor = computed(() => props.category?.color)
const used = computed(() => (props.category?.transactions_count ?? 0) > 0)
const kindOptions = computed(() => [
  { value: 'expense' as const, label: t('finance.categoryKinds.expense') },
  { value: 'income' as const, label: t('finance.categoryKinds.income') },
])

async function submit() {
  try {
    const body =
      props.category && used.value
        ? { name: name.value, icon: icon.value, color: color.value }
        : { name: name.value, kind: categoryKind.value, icon: icon.value, color: color.value }
    await save.mutateAsync({ id: props.category?.id, body })
    toast.show({ title: t('finance.categories.saved') })
    emit('close')
  } catch (error) {
    capture(error)
  }
}

async function archiveIt() {
  if (!props.category) return
  try {
    await archive.mutateAsync({ id: props.category.id, archived: true })
    toast.show({ title: t('finance.categories.archivedToast') })
    emit('close')
  } catch (error) {
    capture(error)
  }
}

async function deleteIt() {
  if (!props.category) return
  try {
    await remove.mutateAsync(props.category.id)
    toast.show({ title: t('finance.categories.deleted') })
    confirmOpen.value = false
    emit('close')
  } catch (error) {
    confirmOpen.value = false
    capture(error)
  }
}
</script>

<template>
  <PCard
    as="form"
    :title="category ? t('finance.categories.editTitle') : t('finance.categories.newTitle')"
    novalidate
    @submit.prevent="submit"
  >
    <template #actions>
      <PIconButton icon="close" :label="t('finance.actions.close')" @click="emit('close')" />
    </template>
    <div class="form">
      <PPanel class="form__preview">
        <PTile :icon="dataIcon(icon)" :tone="colorTone(color)" size="lg" />
        <span class="form__preview-text">
          <PText variant="h3" as="span">{{ name || t('finance.categories.name') }}</PText>
          <PText variant="sm" tone="muted" as="span">{{ t('finance.categories.preview') }}</PText>
        </span>
      </PPanel>
      <PAlert v-if="failure" :title="failure" />
      <PField :label="t('finance.categories.name')" :error="errors.name">
        <PInput v-model="name" :maxlength="40" />
      </PField>
      <PField
        :label="t('finance.categories.kind')"
        label-as="span"
        :hint="used ? t('finance.categories.kindLocked') : undefined"
      >
        <PSegmented
          v-model="categoryKind"
          :options="kindOptions"
          :label="t('finance.categories.kind')"
          :disabled="used"
          block
        />
      </PField>
      <PField :label="t('finance.categories.icon')" label-as="span">
        <PIconPicker
          v-model="icon"
          :options="iconOptions(CATEGORY_ICONS, t, category?.icon)"
          :label="t('finance.categories.icon')"
          :tone="colorTone(color)"
        />
      </PField>
      <PField :label="t('finance.categories.color')" label-as="span">
        <PSwatchPicker
          v-model="color"
          :options="swatchOptions(t, initialColor)"
          :label="t('finance.categories.color')"
        />
      </PField>
      <div class="form__actions">
        <template v-if="category">
          <PButton
            v-if="used"
            variant="ghost"
            class="form__footer-start"
            :loading="archive.isPending.value"
            @click="archiveIt"
            >{{ t('finance.actions.archive') }}</PButton
          >
          <PButton v-else variant="ghost" class="form__footer-start" @click="confirmOpen = true">{{
            t('finance.actions.delete')
          }}</PButton>
        </template>
        <PButton @click="emit('close')">{{ t('ui.cancel') }}</PButton>
        <PButton type="submit" variant="primary" :loading="save.isPending.value">{{
          category ? t('ui.save') : t('finance.categories.create')
        }}</PButton>
      </div>
      <PText v-if="category" variant="sm" tone="muted">{{
        used
          ? t('finance.categories.archiveNote', category.transactions_count)
          : t('finance.categories.deleteNote')
      }}</PText>
    </div>
    <PConfirmDialog
      v-model:open="confirmOpen"
      :title="t('finance.actions.delete')"
      :description="category?.name ?? ''"
      :confirm-label="t('finance.actions.delete')"
      :loading="remove.isPending.value"
      @confirm="deleteIt"
    />
  </PCard>
</template>

<style src="./form.css" scoped></style>
