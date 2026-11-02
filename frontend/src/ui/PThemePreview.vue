<script setup lang="ts">
/** Miniature of the interface in a theme. Draws with the real tokens of that theme. */
defineProps<{ theme: 'light' | 'dark' | 'system' }>()
</script>

<template>
  <span v-if="theme === 'system'" class="p-theme-preview p-theme-preview--split" aria-hidden="true">
    <span data-theme="light" class="p-theme-preview__half" />
    <span data-theme="dark" class="p-theme-preview__half" />
  </span>
  <span
    v-else
    :data-theme="theme"
    class="p-theme-preview"
    :class="`p-theme-preview--${theme}`"
    aria-hidden="true"
  >
    <span class="p-theme-preview__rail" />
    <span class="p-theme-preview__main">
      <span class="p-theme-preview__title" />
      <span class="p-theme-preview__card" />
    </span>
  </span>
</template>

<style scoped>
.p-theme-preview {
  display: flex;
  gap: var(--space-2);
  height: 84px;
  padding: var(--space-2-5);
  border-radius: var(--radius-md);
  background: var(--color-bg);
}

.p-theme-preview--light,
.p-theme-preview--split {
  border: 1px solid var(--color-border);
}

.p-theme-preview--split {
  padding: 0;
  overflow: hidden;
  gap: 0;
}

.p-theme-preview__half {
  flex: 1;
  background: var(--color-bg);
}

.p-theme-preview__rail {
  width: 14px;
  border-radius: var(--radius-xs);
  background: var(--color-text);
}

.p-theme-preview__main {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--space-1-5);
}

.p-theme-preview__title {
  width: 60%;
  height: 10px;
  border-radius: var(--radius-2xs);
  background: var(--color-text);
}

.p-theme-preview__card {
  flex: 1;
  border-radius: var(--radius-sm);
  background: var(--color-surface);
}
</style>
