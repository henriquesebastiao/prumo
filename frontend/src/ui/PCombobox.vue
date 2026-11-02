<script setup lang="ts">
import {
  ComboboxAnchor,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxPortal,
  ComboboxRoot,
  ComboboxViewport,
} from 'reka-ui'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useField } from './field'
import PIcon from './PIcon.vue'
import type { Option } from './types'

const props = withDefaults(
  defineProps<{
    options: Option[]
    placeholder?: string
    invalid?: boolean
    /** Label for the "create" item, receives the typed text: `Cadastrar nova oficina “{term}”`. */
    createLabel?: (term: string) => string
    id?: string
    portal?: boolean
  }>(),
  { placeholder: undefined, createLabel: undefined, id: undefined, portal: true },
)

const emit = defineEmits<{ create: [term: string] }>()
const model = defineModel<string | null>({ default: null })
const search = ref('')
const field = useField(props)
const { t } = useI18n()

const CREATE = '__p-create__'
const term = computed(() => search.value.trim())
const filtered = computed(() => {
  const needle = term.value.toLocaleLowerCase()
  return needle
    ? props.options.filter((option) => option.label.toLocaleLowerCase().includes(needle))
    : props.options
})
const canCreate = computed(
  () =>
    Boolean(props.createLabel && term.value) &&
    !props.options.some((o) => o.label.toLocaleLowerCase() === term.value.toLocaleLowerCase()),
)
const selected = computed({
  get: () => model.value ?? undefined,
  set: (value: string | undefined) => {
    if (value === CREATE) emit('create', term.value)
    else model.value = value ?? null
  },
})

function displayValue(value: unknown): string {
  return props.options.find((option) => option.value === value)?.label ?? ''
}
</script>

<template>
  <ComboboxRoot v-model="selected" ignore-filter>
    <ComboboxAnchor class="p-control" :class="{ 'p-control--invalid': field.invalid.value }">
      <ComboboxInput
        :id="field.id.value"
        v-model="search"
        class="p-control__input"
        :placeholder="placeholder"
        :display-value="displayValue"
        :aria-invalid="field.invalid.value || undefined"
        :aria-describedby="field.describedBy.value"
      />
      <PIcon name="chevron-down" size="sm" class="p-control__icon" />
    </ComboboxAnchor>
    <ComboboxPortal :disabled="!portal">
      <ComboboxContent class="p-options" position="popper" :side-offset="6">
        <ComboboxViewport>
          <ComboboxEmpty v-if="!canCreate" class="p-options__empty">{{
            t('ui.noResults')
          }}</ComboboxEmpty>
          <ComboboxItem
            v-for="option in filtered"
            :key="option.value"
            :value="option.value"
            class="p-options__item"
          >
            <span class="p-options__text">
              {{ option.label }}
              <span v-if="option.description" class="p-options__description">{{
                option.description
              }}</span>
            </span>
          </ComboboxItem>
          <ComboboxItem v-if="canCreate" :value="CREATE" class="p-options__item">
            <PIcon name="add" size="sm" />
            <span class="p-options__text">{{ createLabel?.(term) }}</span>
          </ComboboxItem>
        </ComboboxViewport>
      </ComboboxContent>
    </ComboboxPortal>
  </ComboboxRoot>
</template>

<style src="./control.css"></style>
