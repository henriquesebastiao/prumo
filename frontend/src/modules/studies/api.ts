/** Queries and mutations of the studies module (TanStack Query). Keys start with `studies`. */
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import { api, unwrap, type Schemas } from '@/lib/api/client'

export type Area = Schemas['AreaRead']
export type Subject = Schemas['SubjectRead']
export type SubjectDetail = Schemas['SubjectDetail']
export type SubjectRef = Schemas['SubjectRef']
export type Plan = Schemas['PlanRead']
export type PlanBlock = Schemas['BlockRead']
export type BlockWrite = Schemas['BlockWrite']
export type StudySession = Schemas['StudySessionRead']
export type Day = Schemas['DayRead']
export type DayRow = Schemas['DayRow']
export type Week = Schemas['WeekRead']
export type DayStatus = Schemas['DayStatus']
export type StudiesSummary = Schemas['StudiesSummary']

const ALL = 200

export const studiesKeys = {
  all: ['studies'] as const,
  areas: (archived: string) => ['studies', 'areas', archived] as const,
  subjects: (filters: object) => ['studies', 'subjects', filters] as const,
  subject: (id: string) => ['studies', 'subject', id] as const,
  plans: ['studies', 'plans'] as const,
  day: (on: string | undefined) => ['studies', 'day', on ?? 'today'] as const,
  week: (start: string | undefined) => ['studies', 'week', start ?? 'current'] as const,
  sessions: (filters: object) => ['studies', 'sessions', filters] as const,
}

/** Every studies mutation changes derived values (goals, statuses, week) and Início. */
function useInvalidateStudies() {
  const client = useQueryClient()
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: studiesKeys.all }),
      client.invalidateQueries({ queryKey: ['dashboard'] }),
    ])
}

// ---------------------------------------------------------------- reads

export function useAreas(archived: MaybeRefOrGetter<'false' | 'true' | 'all'> = 'false') {
  return useQuery({
    queryKey: computed(() => studiesKeys.areas(toValue(archived))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/studies/areas', {
          params: { query: { archived: toValue(archived), limit: ALL } },
        }),
      ),
    select: (page) => page.items,
  })
}

export interface SubjectFilters {
  area_id?: string
  archived?: 'false' | 'true' | 'all'
  q?: string
}

export function useSubjects(filters: MaybeRefOrGetter<SubjectFilters> = {}) {
  return useQuery({
    queryKey: computed(() => studiesKeys.subjects(toValue(filters))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/studies/subjects', {
          params: { query: { ...toValue(filters), limit: ALL } },
        }),
      ),
    select: (page) => page.items,
  })
}

export function useSubject(id: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => studiesKeys.subject(toValue(id))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/studies/subjects/{subject_id}', {
          params: { path: { subject_id: toValue(id) } },
        }),
      ),
  })
}

export function usePlans() {
  return useQuery({
    queryKey: studiesKeys.plans,
    queryFn: () => unwrap(api.GET('/api/v1/studies/plans')),
  })
}

export function useDay(on: MaybeRefOrGetter<string | undefined> = undefined) {
  return useQuery({
    queryKey: computed(() => studiesKeys.day(toValue(on))),
    queryFn: () => {
      const value = toValue(on)
      return unwrap(
        api.GET('/api/v1/studies/day', { params: { query: value ? { on: value } : {} } }),
      )
    },
  })
}

export function useWeek(start: MaybeRefOrGetter<string | undefined> = undefined) {
  return useQuery({
    queryKey: computed(() => studiesKeys.week(toValue(start))),
    queryFn: () => {
      const value = toValue(start)
      return unwrap(
        api.GET('/api/v1/studies/week', { params: { query: value ? { start: value } : {} } }),
      )
    },
    placeholderData: (previous) => previous,
  })
}

export interface SessionFilters {
  subject_id?: string
  from?: string
  to?: string
}

export function useSessions(filters: MaybeRefOrGetter<SessionFilters> = {}) {
  return useQuery({
    queryKey: computed(() => studiesKeys.sessions(toValue(filters))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/studies/sessions', {
          params: { query: { ...toValue(filters), limit: ALL } },
        }),
      ),
    select: (page) => page.items,
  })
}

// ---------------------------------------------------------------- mutations

export function useSaveArea() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['AreaCreate'] | Schemas['AreaUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/studies/areas/{area_id}', {
              params: { path: { area_id: id } },
              body: body as Schemas['AreaUpdate'],
            }),
          )
        : unwrap(api.POST('/api/v1/studies/areas', { body: body as Schemas['AreaCreate'] })),
    onSuccess: invalidate,
  })
}

export function useArchiveArea() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: ({ id, archived }: { id: string; archived: boolean }) =>
      archived
        ? unwrap(
            api.POST('/api/v1/studies/areas/{area_id}/archive', {
              params: { path: { area_id: id } },
            }),
          )
        : unwrap(
            api.POST('/api/v1/studies/areas/{area_id}/unarchive', {
              params: { path: { area_id: id } },
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteArea() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE('/api/v1/studies/areas/{area_id}', { params: { path: { area_id: id } } })),
    onSuccess: invalidate,
  })
}

export function useSaveSubject() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['SubjectCreate'] | Schemas['SubjectUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/studies/subjects/{subject_id}', {
              params: { path: { subject_id: id } },
              body: body as Schemas['SubjectUpdate'],
            }),
          )
        : unwrap(api.POST('/api/v1/studies/subjects', { body: body as Schemas['SubjectCreate'] })),
    onSuccess: invalidate,
  })
}

export function useArchiveSubject() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: ({ id, archived }: { id: string; archived: boolean }) =>
      archived
        ? unwrap(
            api.POST('/api/v1/studies/subjects/{subject_id}/archive', {
              params: { path: { subject_id: id } },
            }),
          )
        : unwrap(
            api.POST('/api/v1/studies/subjects/{subject_id}/unarchive', {
              params: { path: { subject_id: id } },
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteSubject() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/studies/subjects/{subject_id}', {
          params: { path: { subject_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useDeleteTopic() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/studies/topics/{topic_id}', { params: { path: { topic_id: id } } }),
      ),
    onSuccess: invalidate,
  })
}

export function useSavePlan() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: ({
      id,
      valid_from,
      blocks,
    }: {
      id?: string
      valid_from: string
      blocks: BlockWrite[]
    }) =>
      id
        ? unwrap(
            api.PUT('/api/v1/studies/plans/{plan_id}', {
              params: { path: { plan_id: id } },
              body: { blocks },
            }),
          )
        : unwrap(api.POST('/api/v1/studies/plans', { body: { valid_from, blocks } })),
    onSuccess: invalidate,
  })
}

export function useDeletePlan() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE('/api/v1/studies/plans/{plan_id}', { params: { path: { plan_id: id } } })),
    onSuccess: invalidate,
  })
}

export function useSaveSession() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['StudySessionCreate'] | Schemas['StudySessionUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/studies/sessions/{session_id}', {
              params: { path: { session_id: id } },
              body: body as Schemas['StudySessionUpdate'],
            }),
          )
        : unwrap(
            api.POST('/api/v1/studies/sessions', { body: body as Schemas['StudySessionCreate'] }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteSession() {
  const invalidate = useInvalidateStudies()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/studies/sessions/{session_id}', {
          params: { path: { session_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}
