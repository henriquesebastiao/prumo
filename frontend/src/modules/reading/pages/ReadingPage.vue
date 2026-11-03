<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterView, useRoute } from 'vue-router'

import { PButton, PPageHeader, PSearchField, PSelect, PTabs } from '@/ui'

import BookDialog from '../forms/BookDialog.vue'
import { provideReading } from './context'

const { t } = useI18n()
const route = useRoute()
const creating = ref(false)

const search = ref('')
const query = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
watch(search, (value) => {
  clearTimeout(timer)
  timer = setTimeout(() => (query.value = value.trim()), 300)
})
const owned = ref<'all' | 'yes' | 'no'>('all')
provideReading({ query, owned })

const current = computed(() => String(route.name ?? 'reading.home'))
const onNotes = computed(() => current.value === 'reading.notes')
watch(onNotes, () => {
  search.value = ''
  query.value = ''
})
const ownedOptions = computed(() => [
  { value: 'all' as const, label: t('reading.shelf.ownedAll') },
  { value: 'yes' as const, label: t('reading.shelf.ownedYes') },
  { value: 'no' as const, label: t('reading.shelf.ownedNo') },
])
const tabs = computed(() => [
  { value: 'reading.home', label: t('reading.tabs.shelf'), to: { name: 'reading.home' } },
  { value: 'reading.notes', label: t('reading.tabs.notes'), to: { name: 'reading.notes' } },
])
</script>

<template>
  <PPageHeader
    :overline="t('reading.nav')"
    :title="onNotes ? t('reading.titles.notes') : t('reading.titles.shelf')"
  >
    <div class="reading__search">
      <PSearchField
        v-model="search"
        :placeholder="onNotes ? t('reading.search.notes') : t('reading.search.books')"
      />
    </div>
    <PButton variant="primary" icon="add" @click="creating = true">{{
      t('reading.actions.add')
    }}</PButton>
  </PPageHeader>
  <div class="reading__tabs">
    <PTabs mode="nav" :items="tabs" :model-value="current" :label="t('reading.tabs.label')" />
    <div v-if="!onNotes" class="reading__filter">
      <PSelect v-model="owned" :options="ownedOptions" variant="filter" />
    </div>
  </div>
  <RouterView />
  <BookDialog v-model:open="creating" />
</template>

<style scoped>
.reading__search {
  width: 330px;
  flex: none;
}

@media (width < 700px) {
  .reading__search {
    width: 100%;
  }
}

.reading__tabs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.reading__filter {
  width: 190px;
}
</style>
