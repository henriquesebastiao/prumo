<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { PButton, PCard, PEmptyState, PQueryState, PText } from '@/ui'

import { useAllNotes } from '../api'
import NoteCard from '../components/NoteCard.vue'
import { useReading } from './context'

const { t } = useI18n()
const { query } = useReading()
const notes = useAllNotes(query)
const items = computed(() => notes.data.value?.pages.flatMap((page) => page.items) ?? [])
const total = computed(() => notes.data.value?.pages[0]?.total ?? 0)
</script>

<template>
  <PCard as="div">
    <PQueryState
      :loading="notes.isPending.value"
      :error="notes.error.value"
      :empty="items.length === 0"
    >
      <div class="notes">
        <NoteCard v-for="note in items" :key="note.id" :note="note" show-book />
        <div class="notes__footer">
          <PText variant="sm" tone="muted">{{ items.length }} / {{ total }}</PText>
          <PButton
            v-if="notes.hasNextPage.value"
            :loading="notes.isFetchingNextPage.value"
            @click="notes.fetchNextPage()"
            >{{ t('reading.actions.loadMore') }}</PButton
          >
        </div>
      </div>
      <template #empty>
        <PEmptyState
          :title="t('reading.note.empty')"
          :description="t('reading.note.emptyHint')"
          icon="note"
          tone="reading"
        />
      </template>
    </PQueryState>
  </PCard>
</template>

<style scoped>
.notes {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.notes__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
</style>
