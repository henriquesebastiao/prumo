/** Queries and mutations of the habits module (TanStack Query). Keys start with `habits`. */
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import { api, unwrap, type Schemas } from '@/lib/api/client'

export type Habit = Schemas['HabitRead']
export type HabitDetail = Schemas['HabitDetail']
export type HabitRef = Schemas['HabitRef']
export type HabitFrequency = Schemas['HabitFrequencyRead']
export type HabitPause = Schemas['HabitPauseRead']
export type Relapse = Schemas['RelapseRead']
export type HabitCalendar = Schemas['HabitCalendar']
export type HabitsToday = Schemas['HabitsToday']
export type HabitTodayItem = Schemas['HabitTodayItem']
export type HabitsSummary = Schemas['HabitsSummary']
export type FrequencyKind = Schemas['HabitFrequencyKind']
export type HabitColor = NonNullable<Schemas['HabitCreate']['color']>

const ALL = 200

export const habitsKeys = {
  all: ['habits'] as const,
  list: (archived: string) => ['habits', 'list', archived] as const,
  habit: (id: string) => ['habits', 'habit', id] as const,
  calendar: (id: string, month: string | undefined) =>
    ['habits', 'calendar', id, month ?? 'current'] as const,
  today: ['habits', 'today'] as const,
}

/** Every habits write changes derived values (streaks, rates, today) and Início. */
function useInvalidateHabits() {
  const client = useQueryClient()
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: habitsKeys.all }),
      client.invalidateQueries({ queryKey: ['dashboard'] }),
    ])
}

// ---------------------------------------------------------------- reads

export function useHabits(archived: MaybeRefOrGetter<'false' | 'true' | 'all'> = 'false') {
  return useQuery({
    queryKey: computed(() => habitsKeys.list(toValue(archived))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/habits', {
          params: { query: { archived: toValue(archived), limit: ALL } },
        }),
      ),
    select: (page) => page.items,
  })
}

export function useHabit(id: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => habitsKeys.habit(toValue(id))),
    queryFn: () =>
      unwrap(api.GET('/api/v1/habits/{habit_id}', { params: { path: { habit_id: toValue(id) } } })),
  })
}

export function useCalendar(
  id: MaybeRefOrGetter<string>,
  month: MaybeRefOrGetter<string | undefined>,
  enabled: MaybeRefOrGetter<boolean> = true,
) {
  return useQuery({
    queryKey: computed(() => habitsKeys.calendar(toValue(id), toValue(month))),
    queryFn: () => {
      const value = toValue(month)
      return unwrap(
        api.GET('/api/v1/habits/{habit_id}/calendar', {
          params: { path: { habit_id: toValue(id) }, query: value ? { month: value } : {} },
        }),
      )
    },
    enabled: computed(() => toValue(enabled)),
    placeholderData: (previous) => previous,
  })
}

export function useToday() {
  return useQuery({
    queryKey: habitsKeys.today,
    queryFn: () => unwrap(api.GET('/api/v1/habits/today')),
  })
}

// ---------------------------------------------------------------- mutations

export function useSaveHabit() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['HabitCreate'] | Schemas['HabitUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/habits/{habit_id}', {
              params: { path: { habit_id: id } },
              body: body as Schemas['HabitUpdate'],
            }),
          )
        : unwrap(api.POST('/api/v1/habits', { body: body as Schemas['HabitCreate'] })),
    onSuccess: invalidate,
  })
}

export function useArchiveHabit() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: ({ id, archived }: { id: string; archived: boolean }) =>
      archived
        ? unwrap(
            api.POST('/api/v1/habits/{habit_id}/archive', { params: { path: { habit_id: id } } }),
          )
        : unwrap(
            api.POST('/api/v1/habits/{habit_id}/unarchive', {
              params: { path: { habit_id: id } },
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteHabit() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE('/api/v1/habits/{habit_id}', { params: { path: { habit_id: id } } })),
    onSuccess: invalidate,
  })
}

/** H1, H3: marks a day with a value (`check` sends 1), or unmarks it with `null`. */
export function useMark() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: ({ id, on, value }: { id: string; on: string; value: number | null }) =>
      value === null
        ? unwrap(
            api.DELETE('/api/v1/habits/{habit_id}/entries/{on}', {
              params: { path: { habit_id: id, on } },
            }),
          )
        : unwrap(
            api.PUT('/api/v1/habits/{habit_id}/entries/{on}', {
              params: { path: { habit_id: id, on } },
              body: { value },
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useSaveFrequency() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: ({
      habitId,
      id,
      body,
    }: {
      habitId: string
      id?: string
      body: Schemas['HabitFrequencyCreate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/habits/frequencies/{frequency_id}', {
              params: { path: { frequency_id: id } },
              body: {
                kind: body.kind,
                times_per_week: body.times_per_week,
                weekdays: body.weekdays,
              },
            }),
          )
        : unwrap(
            api.POST('/api/v1/habits/{habit_id}/frequencies', {
              params: { path: { habit_id: habitId } },
              body,
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteFrequency() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/habits/frequencies/{frequency_id}', {
          params: { path: { frequency_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useSavePause() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: ({
      habitId,
      id,
      body,
    }: {
      habitId: string
      id?: string
      body: Schemas['HabitPauseCreate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/habits/pauses/{pause_id}', {
              params: { path: { pause_id: id } },
              body: { starts_on: body.starts_on, ends_on: body.ends_on ?? null },
            }),
          )
        : unwrap(
            api.POST('/api/v1/habits/{habit_id}/pauses', {
              params: { path: { habit_id: habitId } },
              body,
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeletePause() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/habits/pauses/{pause_id}', { params: { path: { pause_id: id } } }),
      ),
    onSuccess: invalidate,
  })
}

export function useLogRelapse() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: ({ habitId, body }: { habitId: string; body: Schemas['RelapseCreate'] }) =>
      unwrap(
        api.POST('/api/v1/habits/{habit_id}/relapses', {
          params: { path: { habit_id: habitId } },
          body,
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useDeleteRelapse() {
  const invalidate = useInvalidateHabits()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/habits/relapses/{relapse_id}', {
          params: { path: { relapse_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}
