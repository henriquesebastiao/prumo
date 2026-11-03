<script setup lang="ts">
/**
 * A book cover: the uploaded image, or one drawn with the title and the author. `variant`
 * picks the look of the drawn cover (module tone, neutral paper or ink).
 */
import { ref, watch } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

import type { Tone } from './types'

const props = withDefaults(
  defineProps<{
    title: string
    author?: string
    src?: string
    variant?: 'tone' | 'paper' | 'ink'
    size?: 'sm' | 'md' | 'lg' | 'xl'
    tone?: Tone
    /** Makes the cover a link (to the book). */
    to?: RouteLocationRaw
  }>(),
  {
    author: undefined,
    src: undefined,
    variant: 'tone',
    size: 'md',
    tone: 'reading',
    to: undefined,
  },
)

/** Falls back to the drawn cover when the image cannot be loaded. */
const failed = ref(false)
watch(
  () => props.src,
  () => (failed.value = false),
)
</script>

<template>
  <component
    :is="to ? RouterLink : 'div'"
    :to="to"
    :aria-label="to ? title : undefined"
    class="p-book-cover"
    :class="[`p-book-cover--${size}`, `p-book-cover--${variant}`]"
    :data-tone="tone"
  >
    <img
      v-if="src && !failed"
      :src="src"
      :alt="title"
      class="p-book-cover__image"
      loading="lazy"
      @error="failed = true"
    />
    <template v-else>
      <span class="p-book-cover__title">{{ title }}</span>
      <span v-if="author" class="p-book-cover__author">{{ author }}</span>
    </template>
  </component>
</template>

<style scoped>
.p-book-cover {
  position: relative;
  display: flex;
  overflow: hidden;
  flex: none;
  flex-direction: column;
  justify-content: space-between;
  border-radius: var(--radius-md);
  aspect-ratio: 0.68;
  box-shadow: var(--shadow-sm);
  text-decoration: none;
}

a.p-book-cover:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

.p-book-cover::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 7%;
  background: var(--cover-spine);
  content: '';
}

.p-book-cover--sm {
  width: 72px;
  padding: var(--space-2) var(--space-2) var(--space-2) var(--space-3);
  font-size: var(--text-2xs);
}

.p-book-cover--md {
  width: 100px;
  padding: var(--space-3) var(--space-2-5) var(--space-3) var(--space-3-5);
  font-size: var(--text-sm);
}

.p-book-cover--lg {
  width: 140px;
  padding: var(--space-4) var(--space-3-5) var(--space-4) var(--space-5);
  font-size: var(--text-xl);
}

.p-book-cover--xl {
  width: 184px;
  padding: var(--space-5) var(--space-4) var(--space-5) var(--space-6);
  font-size: var(--text-2xl);
}

.p-book-cover--tone {
  --cover-spine: var(--tone-soft);

  background: var(--tone-container);
  color: var(--tone);
}

.p-book-cover--paper {
  --cover-spine: var(--color-border-strong);

  background: var(--color-border);
  color: var(--color-text);
}

.p-book-cover--ink {
  --cover-spine: var(--color-text-secondary);

  background: var(--color-accent);
  color: var(--color-accent-contrast);
}

.p-book-cover__title {
  overflow: hidden;
  font-weight: var(--weight-heavy);
  letter-spacing: var(--tracking-snug);
  line-height: var(--leading-tight);
}

.p-book-cover__author {
  font-size: 0.75em;
  font-weight: var(--weight-bold);
  line-height: var(--leading-snug);
}

.p-book-cover--lg .p-book-cover__author,
.p-book-cover--xl .p-book-cover__author {
  font-size: var(--text-md);
}

.p-book-cover__image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
