<script setup lang="ts" generic="Row extends Record<string, unknown>">
defineProps<{
  columns: { key: string; label: string; align?: 'start' | 'end'; hideLabel?: boolean }[]
  /** Rows, or groups of rows with a label (e.g. transactions by day). */
  rows?: Row[]
  groups?: { label: string; rows: Row[] }[]
  rowKey: (row: Row) => string
  caption?: string
}>()
</script>

<template>
  <div class="p-table">
    <table class="p-table__table">
      <caption v-if="caption" class="p-sr-only">
        {{
          caption
        }}
      </caption>
      <thead>
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            scope="col"
            :class="{ 'p-table__end': column.align === 'end' }"
          >
            <span :class="{ 'p-sr-only': column.hideLabel }">{{ column.label }}</span>
          </th>
        </tr>
      </thead>
      <tbody v-if="rows">
        <tr v-for="row in rows" :key="rowKey(row)">
          <td
            v-for="column in columns"
            :key="column.key"
            :data-label="column.label"
            :class="{ 'p-table__end': column.align === 'end' }"
          >
            <slot :name="`cell-${column.key}`" :row="row">{{ row[column.key] }}</slot>
          </td>
        </tr>
      </tbody>
      <template v-for="group in groups ?? []" :key="group.label">
        <tbody>
          <tr class="p-table__group">
            <th :colspan="columns.length" scope="rowgroup">{{ group.label }}</th>
          </tr>
          <tr v-for="row in group.rows" :key="rowKey(row)">
            <td
              v-for="column in columns"
              :key="column.key"
              :data-label="column.label"
              :class="{ 'p-table__end': column.align === 'end' }"
            >
              <slot :name="`cell-${column.key}`" :row="row">{{ row[column.key] }}</slot>
            </td>
          </tr>
        </tbody>
      </template>
    </table>
  </div>
</template>

<style scoped>
.p-table {
  overflow-x: auto;
  container-type: inline-size;
}

.p-table__table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-md);
}

th {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-divider);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-align: left;
  white-space: nowrap;
}

td {
  padding: 11px var(--space-3);
  border-bottom: 1px solid var(--color-divider);
  vertical-align: middle;
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr:not(.p-table__group):hover {
  background: var(--color-surface-inset);
}

.p-table__end {
  text-align: right;
  white-space: nowrap;
}

.p-table__group th {
  padding: var(--space-3-5) var(--space-3) var(--space-1-5);
  border-bottom: 0;
  font-weight: var(--weight-bold);
}

/* Narrow containers (phones): each row becomes a block, cells stack with their labels. */
@container (width < 560px) {
  thead {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
  }

  tr {
    display: block;
    padding: var(--space-2-5) 0;
    border-bottom: 1px solid var(--color-divider);
  }

  td {
    display: flex;
    justify-content: space-between;
    gap: var(--space-3);
    padding: var(--space-0-5) 0;
    border: 0;
  }

  td::before {
    color: var(--color-text-muted);
    font-size: var(--text-xs);
    content: attr(data-label);
  }

  .p-table__end {
    text-align: right;
  }
}
</style>
