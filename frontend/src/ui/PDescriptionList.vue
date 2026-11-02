<script setup lang="ts">
defineProps<{ items: { label: string; value: string }[] }>()
</script>

<template>
  <dl class="p-dl">
    <div v-for="item in items" :key="item.label" class="p-dl__row">
      <dt>{{ item.label }}</dt>
      <dd>{{ item.value }}</dd>
    </div>
  </dl>
</template>

<style scoped>
.p-dl {
  display: flex;
  flex-direction: column;
  gap: var(--space-1-5);
  font-size: var(--text-md);
}

.p-dl__row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-inset);
}

.p-dl dt {
  color: var(--color-text-muted);
}

.p-dl dd {
  margin: 0;
  font-weight: var(--weight-bold);
  text-align: right;
}
</style>
