/** Queries and mutations of the garage module (TanStack Query). Keys start with `garage`. */
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import { api, unwrap, type Schemas } from '@/lib/api/client'

export type Vehicle = Schemas['VehicleRead']
export type Maintenance = Schemas['MaintenanceRead']
export type Fueling = Schemas['FuelingRead']
export type Workshop = Schemas['WorkshopRead']
export type Reading = Schemas['OdometerReadingRead']
export type GarageSummary = Schemas['GarageSummary']

const PAGE = 50
const ALL = 200

export const garageKeys = {
  all: ['garage'] as const,
  overview: ['garage', 'overview'] as const,
  vehicles: (archived: string) => ['garage', 'vehicles', archived] as const,
  vehicle: (id: string) => ['garage', 'vehicle', id] as const,
  readings: (id: string) => ['garage', 'vehicle', id, 'odometer'] as const,
  maintenances: (filters: object) => ['garage', 'maintenances', filters] as const,
  maintenance: (vehicleId: string, id: string) => ['garage', 'maintenance', vehicleId, id] as const,
  fuelings: (filters: object) => ['garage', 'fuelings', filters] as const,
  workshops: ['garage', 'workshops'] as const,
  suggestion: (id: string, km: number | null, on: string | null) =>
    ['garage', 'vehicle', id, 'suggestion', km, on] as const,
}

/** Every garage mutation changes derived values (km, oil status, stats) and Início. */
function useInvalidateGarage() {
  const client = useQueryClient()
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: garageKeys.all }),
      client.invalidateQueries({ queryKey: ['dashboard'] }),
    ])
}

// ---------------------------------------------------------------- reads

export function useOverview() {
  return useQuery({
    queryKey: garageKeys.overview,
    queryFn: () => unwrap(api.GET('/api/v1/garage/overview')),
  })
}

export function useVehicles(archived: 'false' | 'true' | 'all' = 'false') {
  return useQuery({
    queryKey: garageKeys.vehicles(archived),
    queryFn: () =>
      unwrap(api.GET('/api/v1/garage/vehicles', { params: { query: { archived, limit: ALL } } })),
    select: (page) => page.items,
  })
}

export function useVehicle(id: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => garageKeys.vehicle(toValue(id))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/garage/vehicles/{vehicle_id}', {
          params: { path: { vehicle_id: toValue(id) } },
        }),
      ),
  })
}

export function useReadings(id: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => garageKeys.readings(toValue(id))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/garage/vehicles/{vehicle_id}/odometer', {
          params: { path: { vehicle_id: toValue(id) }, query: { limit: ALL } },
        }),
      ),
    select: (page) => page.items,
  })
}

export interface MaintenanceFilters {
  vehicle_id?: string
  kind?: 'general' | 'oil_change'
  workshop_id?: string
}

/** Maintenances of every vehicle (or filtered), loaded page by page. */
export function useMaintenances(filters: MaybeRefOrGetter<MaintenanceFilters>, pageSize = PAGE) {
  return useInfiniteQuery({
    queryKey: computed(() => garageKeys.maintenances({ ...toValue(filters), pageSize })),
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      unwrap(
        api.GET('/api/v1/garage/maintenances', {
          params: { query: { ...toValue(filters), limit: pageSize, offset: pageParam } },
        }),
      ),
    getNextPageParam: (last) =>
      last.offset + last.items.length < last.total ? last.offset + last.items.length : undefined,
  })
}

export interface FuelingFilters {
  vehicle_id?: string
}

export function useFuelings(filters: MaybeRefOrGetter<FuelingFilters>, pageSize = PAGE) {
  return useInfiniteQuery({
    queryKey: computed(() => garageKeys.fuelings({ ...toValue(filters), pageSize })),
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      unwrap(
        api.GET('/api/v1/garage/fuelings', {
          params: { query: { ...toValue(filters), limit: pageSize, offset: pageParam } },
        }),
      ),
    getNextPageParam: (last) =>
      last.offset + last.items.length < last.total ? last.offset + last.items.length : undefined,
  })
}

export function useMaintenance(vehicleId: MaybeRefOrGetter<string>, id: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => garageKeys.maintenance(toValue(vehicleId), toValue(id))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/garage/vehicles/{vehicle_id}/maintenances/{maintenance_id}', {
          params: { path: { vehicle_id: toValue(vehicleId), maintenance_id: toValue(id) } },
        }),
      ),
  })
}

export function useWorkshops() {
  return useQuery({
    queryKey: garageKeys.workshops,
    queryFn: () =>
      unwrap(api.GET('/api/v1/garage/workshops', { params: { query: { limit: ALL } } })),
    select: (page) => page.items,
  })
}

export function useOilSuggestion(
  vehicleId: MaybeRefOrGetter<string | null>,
  km: MaybeRefOrGetter<number | null>,
  on: MaybeRefOrGetter<string | null>,
) {
  return useQuery({
    queryKey: computed(() =>
      garageKeys.suggestion(toValue(vehicleId) ?? '', toValue(km), toValue(on)),
    ),
    enabled: computed(() => Boolean(toValue(vehicleId))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/garage/vehicles/{vehicle_id}/oil-change-suggestion', {
          params: {
            path: { vehicle_id: toValue(vehicleId) ?? '' },
            query: { km: toValue(km) ?? undefined, on: toValue(on) ?? undefined },
          },
        }),
      ),
  })
}

// ---------------------------------------------------------------- mutations

export function useSaveVehicle() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['VehicleCreate'] | Schemas['VehicleUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/garage/vehicles/{vehicle_id}', {
              params: { path: { vehicle_id: id } },
              body: body as Schemas['VehicleUpdate'],
            }),
          )
        : unwrap(api.POST('/api/v1/garage/vehicles', { body: body as Schemas['VehicleCreate'] })),
    onSuccess: invalidate,
  })
}

export function useArchiveVehicle() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: ({ id, archived }: { id: string; archived: boolean }) =>
      archived
        ? unwrap(
            api.POST('/api/v1/garage/vehicles/{vehicle_id}/archive', {
              params: { path: { vehicle_id: id } },
            }),
          )
        : unwrap(
            api.POST('/api/v1/garage/vehicles/{vehicle_id}/unarchive', {
              params: { path: { vehicle_id: id } },
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteVehicle() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/garage/vehicles/{vehicle_id}', {
          params: { path: { vehicle_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useAddReading() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: ({ vehicleId, km }: { vehicleId: string; km: number }) =>
      unwrap(
        api.POST('/api/v1/garage/vehicles/{vehicle_id}/odometer', {
          params: { path: { vehicle_id: vehicleId } },
          body: { km },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useDeleteReading() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: ({ vehicleId, id }: { vehicleId: string; id: string }) =>
      unwrap(
        api.DELETE('/api/v1/garage/vehicles/{vehicle_id}/odometer/{reading_id}', {
          params: { path: { vehicle_id: vehicleId, reading_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useSaveMaintenance() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: ({
      vehicleId,
      id,
      body,
    }: {
      vehicleId: string
      id?: string
      body: Schemas['MaintenanceCreate'] | Schemas['MaintenanceUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/garage/vehicles/{vehicle_id}/maintenances/{maintenance_id}', {
              params: { path: { vehicle_id: vehicleId, maintenance_id: id } },
              body: body as Schemas['MaintenanceUpdate'],
            }),
          )
        : unwrap(
            api.POST('/api/v1/garage/vehicles/{vehicle_id}/maintenances', {
              params: { path: { vehicle_id: vehicleId } },
              body: body as Schemas['MaintenanceCreate'],
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteMaintenance() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: ({ vehicleId, id }: { vehicleId: string; id: string }) =>
      unwrap(
        api.DELETE('/api/v1/garage/vehicles/{vehicle_id}/maintenances/{maintenance_id}', {
          params: { path: { vehicle_id: vehicleId, maintenance_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useSaveFueling() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: ({
      vehicleId,
      id,
      body,
    }: {
      vehicleId: string
      id?: string
      body: Schemas['FuelingCreate'] | Schemas['FuelingUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/garage/vehicles/{vehicle_id}/fuelings/{fueling_id}', {
              params: { path: { vehicle_id: vehicleId, fueling_id: id } },
              body: body as Schemas['FuelingUpdate'],
            }),
          )
        : unwrap(
            api.POST('/api/v1/garage/vehicles/{vehicle_id}/fuelings', {
              params: { path: { vehicle_id: vehicleId } },
              body: body as Schemas['FuelingCreate'],
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteFueling() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: ({ vehicleId, id }: { vehicleId: string; id: string }) =>
      unwrap(
        api.DELETE('/api/v1/garage/vehicles/{vehicle_id}/fuelings/{fueling_id}', {
          params: { path: { vehicle_id: vehicleId, fueling_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useSaveWorkshop() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: ({ id, body }: { id?: string; body: Schemas['WorkshopCreate'] }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/garage/workshops/{workshop_id}', {
              params: { path: { workshop_id: id } },
              body,
            }),
          )
        : unwrap(api.POST('/api/v1/garage/workshops', { body })),
    onSuccess: invalidate,
  })
}

export function useDeleteWorkshop() {
  const invalidate = useInvalidateGarage()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/garage/workshops/{workshop_id}', {
          params: { path: { workshop_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}
