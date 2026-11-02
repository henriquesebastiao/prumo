import type { IconName } from '@/ui'

import type { Vehicle } from './api'

export function vehicleIcon(kind: 'car' | 'motorcycle'): IconName {
  return kind === 'motorcycle' ? 'motorcycle' : 'car'
}

/** The vehicle used most recently (latest km reading): pre-selected when there is no context. */
export function lastUsedVehicle(vehicles: Vehicle[]): Vehicle | undefined {
  return [...vehicles].sort((a, b) => b.current_km_at.localeCompare(a.current_km_at))[0]
}

export const FUEL_TYPES = [
  'gasoline',
  'gasoline_additive',
  'gasoline_premium',
  'ethanol',
  'diesel',
  'cng',
] as const
export type FuelType = (typeof FUEL_TYPES)[number]

export interface WorkshopChoice {
  id?: string
  name?: string
}

export interface ItemDraft {
  key: number
  description: string
  quantity: number | null
  unit_price_cents: number | null
}
