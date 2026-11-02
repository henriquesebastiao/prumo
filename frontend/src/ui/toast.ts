import { ref } from 'vue'

import type { Tone } from './types'

export interface ToastMessage {
  id: number
  title: string
  description?: string
  tone?: Tone
}

const messages = ref<ToastMessage[]>([])
let nextId = 1

/** Short confirmation messages ("Alterações salvas"). Rendered by <PToaster>. */
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
