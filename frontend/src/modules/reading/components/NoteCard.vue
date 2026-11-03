<script setup lang="ts">
/** A note: page, date and text; optionally the book and the row menu. */
import { useI18n } from 'vue-i18n'

import { date } from '@/lib/format'
import { PBadge, PIconButton, PLink, PMenu, PPanel, PText, type MenuEntry } from '@/ui'

import type { Note } from '../api'

defineProps<{ note: Note; showBook?: boolean; menu?: MenuEntry[] }>()
const { t } = useI18n()
</script>

<template>
  <PPanel as="article" class="note">
    <div class="note__head">
      <PBadge :tone="note.page !== null ? 'reading' : 'neutral'">{{
        note.page !== null
          ? t('reading.detail.page', { page: note.page })
          : t('reading.detail.noPage')
      }}</PBadge>
      <PText variant="sm" tone="muted" as="span">{{ date(note.noted_on) }}</PText>
      <span v-if="showBook" class="note__book">
        <PLink :to="{ name: 'reading.book', params: { bookId: note.book.id } }">{{
          note.book.title
        }}</PLink>
      </span>
      <PMenu v-if="menu" :items="menu">
        <template #trigger>
          <PIconButton icon="more" :label="t('reading.actions.more')" size="sm" />
        </template>
      </PMenu>
    </div>
    <PText class="note__content">{{ note.content }}</PText>
  </PPanel>
</template>

<style scoped>
.note {
  display: flex;
  flex-direction: column;
  gap: var(--space-2-5);
}

.note__head {
  display: flex;
  align-items: center;
  gap: var(--space-2-5);
}

.note__book {
  margin-right: auto;
}

.note__head > :last-child {
  margin-left: auto;
}

.note__content {
  white-space: pre-line;
}
</style>
