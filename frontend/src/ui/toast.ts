import { ref } from 'vue'

import type { Tone } from './types'

export interface ToastMessage {
  id: number
  title: string
  description?: string
  tone?: Tone
  /** One action in the toast ("Desfazer"); the toast closes when it runs. */
  action?: { label: string; run: () => void }
}

const messages = ref<ToastMessage[]>([])
let nextId = 1

/** Short confirmation messages ("Alterações salvas"), with an optional action ("Desfazer").
 * Rendered by <PToaster>. */
export function useToast() {
  return {
    messages,
    show(message: Omit<ToastMessage, 'id'>) {
      messages.value = [...messages.value, { ...message, id: nextId++ }]
    },
    dismiss(id: number) {
      messages.value = messages.value.filter((message) => message.id !== id)
    },
  }
}
