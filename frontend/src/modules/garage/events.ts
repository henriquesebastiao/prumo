/** How the garage items of "Vem aí" and "Atividade recente" appear on Início. */
import type { EventView, Translate } from '@/app/registry'
import type { Schemas } from '@/lib/api/client'
import { decimal, km, liters, money, relativeDateTime } from '@/lib/format'

type Data = Record<string, string | number | boolean | null | undefined>

export function describeUpcoming(item: Schemas['UpcomingItem'], t: Translate): EventView | null {
  if (item.kind !== 'garage.oil_change') return null
  const data = (item.data ?? {}) as Data
  let subtitle: string
  if (data.status === 'overdue') subtitle = t('garage.events.overdue')
  else if (data.basis === 'km_pace' && typeof data.pace_km_per_day === 'number')
    subtitle = t('garage.events.byPace', { pace: decimal(data.pace_km_per_day, 0) })
  else if (typeof data.interval_months === 'number')
    subtitle = t('garage.events.byDate', {
      months: t('garage.oil.months', data.interval_months),
    })
  else subtitle = t('garage.events.byDatePlain')
  return {
    title: t('garage.events.oilChange', { vehicle: item.subject }),
    subtitle,
    to: item.entity_id
      ? { name: 'garage.vehicle', params: { vehicleId: item.entity_id } }
      : undefined,
  }
}

export function describeActivity(item: Schemas['ActivityItem'], t: Translate): EventView | null {
  const data = (item.data ?? {}) as Data
  const when = relativeDateTime(item.occurred_at)
  const vehicle = { vehicle: item.subject }
  switch (item.kind) {
    case 'garage.odometer':
      return {
        title: t('garage.events.odometer', vehicle),
        subtitle: when,
        value: typeof data.km === 'number' ? km(data.km) : undefined,
        icon: 'gauge',
        to: item.entity_id
          ? { name: 'garage.vehicle', params: { vehicleId: item.entity_id } }
          : undefined,
      }
    case 'garage.fueling':
      return {
        title: t('garage.events.fueling', vehicle),
        subtitle: typeof data.volume_ml === 'number' ? `${when} · ${liters(data.volume_ml)}` : when,
        value: typeof data.total_cents === 'number' ? money(data.total_cents) : undefined,
        icon: 'fuel',
        to:
          typeof data.vehicle_id === 'string'
            ? { name: 'garage.vehicle', params: { vehicleId: data.vehicle_id } }
            : undefined,
      }
    case 'garage.maintenance': {
      const oil = data.maintenance_kind === 'oil_change'
      return {
        title: t(oil ? 'garage.events.oilChangeDone' : 'garage.events.maintenance', vehicle),
        subtitle: typeof data.workshop === 'string' ? `${when} · ${data.workshop}` : when,
        value: typeof data.total_cents === 'number' ? money(data.total_cents) : undefined,
        icon: oil ? 'droplet' : 'wrench',
        to:
          typeof data.vehicle_id === 'string' && item.entity_id
            ? {
                name: 'garage.maintenance',
                params: { vehicleId: data.vehicle_id, maintenanceId: item.entity_id },
              }
            : undefined,
      }
    }
    default:
      return null
  }
}
