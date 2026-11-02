<template>
  <kbd class="p-kbd"><slot /></kbd>
</template>

<style scoped>
.p-kbd {
  padding: 1px 7px;
  border-radius: var(--radius-xs);
  background: var(--color-fill);
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  white-space: nowrap;
}
</style>
