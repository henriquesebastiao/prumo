<script setup lang="ts">
import { ToastDescription, ToastProvider, ToastRoot, ToastTitle, ToastViewport } from 'reka-ui'

import { useToast } from './toast'

const { messages, dismiss } = useToast()
</script>

<template>
  <ToastProvider :duration="4000" swipe-direction="right">
    <ToastRoot
      v-for="message in messages"
      :key="message.id"
      class="p-toast"
      :data-tone="message.tone ?? 'accent'"
      @update:open="(open) => !open && dismiss(message.id)"
    >
      <ToastTitle class="p-toast__title">{{ message.title }}</ToastTitle>
      <ToastDescription v-if="message.description" class="p-toast__description">{{
        message.description
      }}</ToastDescription>
    </ToastRoot>
    <ToastViewport class="p-toast__viewport" />
  </ToastProvider>
</template>

<style>
/* Not scoped: the content is teleported by Reka, which does not forward the scope id. */
.p-toast__viewport {
  position: fixed;
  z-index: 60;
  right: var(--space-6);
  bottom: var(--space-6);
  display: flex;
  width: min(380px, calc(100vw - 32px));
  flex-direction: column;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
  outline: none;
}

.p-toast {
  display: flex;
  flex-direction: column;
  gap: var(--space-0-5);
  padding: var(--space-3-5) var(--space-4);
  border-radius: var(--radius-alert);
  background: var(--tone-container);
  color: var(--tone-on-container);
  box-shadow: var(--shadow-lg);
}

.p-toast__title {
  font-weight: var(--weight-bold);
}

.p-toast__description {
  font-size: var(--text-sm);
}
</style>
