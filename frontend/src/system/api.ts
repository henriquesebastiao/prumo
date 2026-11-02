/** Queries and mutations of the platform resources (TanStack Query). */
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import { api, unwrap, type Schemas } from '@/lib/api/client'

export const systemKeys = {
  preferences: ['preferences'] as const,
  modules: ['modules'] as const,
  dashboard: ['dashboard'] as const,
  sessions: ['sessions'] as const,
}

export function usePreferences() {
  return useQuery({
    queryKey: systemKeys.preferences,
    queryFn: () => unwrap(api.GET('/api/v1/me/preferences')),
  })
}

export function useUpdatePreferences() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (body: Schemas['PreferencesUpdate']) =>
      unwrap(api.PATCH('/api/v1/me/preferences', { body })),
    onSuccess: (preferences) => {
      client.setQueryData(systemKeys.preferences, preferences)
      void client.invalidateQueries({ queryKey: systemKeys.modules })
      void client.invalidateQueries({ queryKey: systemKeys.dashboard })
    },
  })
}

export function useModules() {
  return useQuery({
    queryKey: systemKeys.modules,
    queryFn: () => unwrap(api.GET('/api/v1/modules')),
    select: (data) => data.items,
  })
}

export function useDashboard() {
  return useQuery({
    queryKey: systemKeys.dashboard,
    queryFn: () => unwrap(api.GET('/api/v1/dashboard')),
  })
}

export function useSessions() {
  return useQuery({
    queryKey: systemKeys.sessions,
    queryFn: () => unwrap(api.GET('/api/v1/auth/sessions')),
    select: (data) => data.items,
  })
}

export function useRevokeSession() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/auth/sessions/{session_id}', { params: { path: { session_id: id } } }),
      ),
    onSuccess: () => client.invalidateQueries({ queryKey: systemKeys.sessions }),
  })
}

export function useUpdateProfile() {
  return useMutation({
    mutationFn: (body: Schemas['UserUpdate']) => unwrap(api.PATCH('/api/v1/me', { body })),
  })
}

export function useChangePassword() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (body: Schemas['PasswordChange']) =>
      unwrap(api.PUT('/api/v1/me/password', { body })),
    onSuccess: () => client.invalidateQueries({ queryKey: systemKeys.sessions }),
  })
}
