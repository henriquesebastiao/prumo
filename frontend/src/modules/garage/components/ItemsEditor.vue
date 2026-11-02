<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { PButton, PIconButton, PInput, PMoneyInput, PNumberInput } from '@/ui'

import type { ItemDraft } from '../helpers'

const items = defineModel<ItemDraft[]>({ required: true })
defineProps<{ errors?: Record<string, string> }>()
const { t } = useI18n()
let nextKey = Date.now()

function add() {
  items.value = [
    ...items.value,
    { key: nextKey++, description: '', quantity: 1, unit_price_cents: null },
  ]
}

function remove(key: number) {
  items.value = items.value.filter((item) => item.key !== key)
}

function update(key: number, patch: Partial<ItemDraft>) {
  items.value = items.value.map((item) => (item.key === key ? { ...item, ...patch } : item))
}
</script>

<template>
  <div class="items">
    <div v-for="(item, index) in items" :key="item.key" class="items__row">
      <PInput
        :model-value="item.description"
        :placeholder="t('garage.form.partName')"
        :invalid="Boolean(errors?.[`items.${index}.description`])"
        class="items__name"
        @update:model-value="update(item.key, { description: $event })"
      />
      <PNumberInput
        :model-value="item.quantity"
        :prefix="t('garage.form.quantity')"
        class="items__quantity"
        @update:model-value="update(item.key, { quantity: $event })"
      />
      <PMoneyInput
        :model-value="item.unit_price_cents"
        class="items__price"
        @update:model-value="update(item.key, { unit_price_cents: $event })"
      />
      <PIconButton icon="close" :label="t('garage.form.removePart')" @click="remove(item.key)" />
    </div>
    <div>
      <PButton variant="tonal" icon="add" @click="add">{{ t('garage.form.addPart') }}</PButton>
    </div>
  </div>
</template>

<style scoped>
.items {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.items__row {
  display: grid;
  align-items: center;
  gap: var(--space-3);
  grid-template-columns: minmax(0, 1fr) 96px 160px auto;
}

@media (width < 600px) {
  .items__row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .items__name {
    grid-column: 1 / -1;
  }
}
</style>
