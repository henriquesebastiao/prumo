import { defineStore } from 'pinia'
import { ref } from 'vue'

import { queryClient } from '@/app/query'
import { api, unwrap, type Schemas } from '@/lib/api/client'
import { isApiError } from '@/lib/api/errors'

type Status = 'unknown' | 'authenticated' | 'anonymous'

/** The authenticated user and the web session (cookie). */
export const useSessionStore = defineStore('session', () => {
  const user = ref<Schemas['UserRead'] | null>(null)
  const status = ref<Status>('unknown')
  let pending: Promise<void> | null = null

  async function fetchMe(): Promise<void> {
    try {
      user.value = await unwrap(api.GET('/api/v1/me'))
      status.value = 'authenticated'
    } catch (error) {
      user.value = null
      status.value = 'anonymous'
      if (!isApiError(error) || error.status !== 401) throw error
    }
  }

  /** Resolves the session once (first navigation). */
  function load(): Promise<void> {
    if (status.value !== 'unknown') return Promise.resolve()
    pending ??= fetchMe().finally(() => {
      pending = null
    })
    return pending
  }

  async function login(credentials: { username: string; password: string; remember: boolean }) {
    const response = await unwrap(
      api.POST('/api/v1/auth/login', { body: { ...credentials, client: 'web' } }),
    )
    user.value = response.user
    status.value = 'authenticated'
  }

  function clear() {
    user.value = null
    status.value = 'anonymous'
    queryClient.clear()
  }

  async function logout() {
    try {
      await unwrap(api.POST('/api/v1/auth/logout'))
    } finally {
      clear()
    }
  }

  function setUser(next: Schemas['UserRead']) {
    user.value = next
  }

  return { user, status, load, login, logout, clear, setUser }
})
