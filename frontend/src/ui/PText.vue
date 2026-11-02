<script setup lang="ts">
/** Text styles of the design. Screens use this instead of styling text themselves. */
withDefaults(
  defineProps<{
    variant?:
      | 'h1'
      | 'title'
      | 'h2'
      | 'h3'
      | 'lead'
      | 'body'
      | 'strong'
      | 'sm'
      | 'xs'
      | 'overline'
      | 'number-xl'
      | 'number-l'
    tone?: 'default' | 'secondary' | 'muted' | 'danger' | 'success'
    weight?: 'regular' | 'medium' | 'semibold' | 'bold'
    as?: string
  }>(),
  { variant: 'body', tone: 'default', weight: undefined, as: 'p' },
)
</script>

<template>
  <component
    :is="as"
    class="p-text"
    :class="[`p-text--${variant}`, `p-text--tone-${tone}`, weight && `p-text--weight-${weight}`]"
    ><slot
  /></component>
</template>

<style scoped>
.p-text {
  min-width: 0;
}

.p-text--h1 {
  font-size: var(--text-4xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

.p-text--title {
  font-size: var(--text-3xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

.p-text--h2 {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-snug);
}

.p-text--h3 {
  font-size: var(--text-base);
  font-weight: var(--weight-bold);
}

.p-text--lead {
  font-size: var(--text-xl);
  text-wrap: pretty;
}

.p-text--strong {
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
}

.p-text--sm {
  font-size: var(--text-sm);
}

.p-text--xs {
  font-size: var(--text-xs);
}

.p-text--overline {
  color: var(--color-text-muted);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
}

.p-text--number-xl,
.p-text--number-l {
  font-family: var(--font-numeric);
  font-weight: var(--weight-heavy);
  letter-spacing: var(--tracking-tight);
  white-space: nowrap;
}

.p-text--number-xl {
  font-size: var(--text-4xl);
  line-height: var(--leading-tight);
}

.p-text--number-l {
  font-size: var(--text-2xl);
  line-height: 1.2;
  letter-spacing: var(--tracking-snug);
}

.p-text--number-xl :deep(small),
.p-text--number-l :deep(small) {
  font-size: 0.53em;
  font-weight: var(--weight-bold);
  letter-spacing: 0;
}

.p-text--tone-secondary {
  color: var(--color-text-secondary);
}

.p-text--tone-muted {
  color: var(--color-text-muted);
}

.p-text--tone-danger {
  color: var(--color-danger);
}

.p-text--tone-success {
  color: var(--color-on-success-container);
}

.p-text--weight-regular {
  font-weight: var(--weight-regular);
}

.p-text--weight-medium {
  font-weight: var(--weight-medium);
}

.p-text--weight-semibold {
  font-weight: var(--weight-semibold);
}

.p-text--weight-bold {
  font-weight: var(--weight-bold);
}
</style>
