<script setup lang="ts">
import { computed } from 'vue'

import { dayMonth } from '@/lib/format'

const props = defineProps<{ date: string | Date }>()
const parts = computed(() => dayMonth(props.date))
</script>

<template>
  <span class="p-date-badge">
    <b>{{ parts.day }}</b>
    <span>{{ parts.month }}</span>
  </span>
</template>

<style scoped>
.p-date-badge {
  display: flex;
  flex: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--color-surface-tint);
  line-height: var(--leading-none);
}

.p-date-badge b {
  font-size: var(--text-lg);
  font-weight: var(--weight-heavy);
}

.p-date-badge span {
  color: var(--color-text-muted);
  font-size: var(--text-2xs);
  font-weight: var(--weight-semibold);
}
</style>
