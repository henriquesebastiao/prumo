import { describe, expect, it } from 'vitest'

import { i18n, loadModuleMessages } from '@/app/i18n'

import garage from '.'
import { describeActivity, describeUpcoming } from './events'

const t = i18n.global.t

describe('garage items on Início', async () => {
  await loadModuleMessages([garage])

  it('describes an oil change by pace or by date', () => {
    const base = {
      module: 'garage',
      kind: 'garage.oil_change',
      on: '2026-11-25',
      subject: 'CG 160',
    }
    expect(
      describeUpcoming({ ...base, data: { basis: 'km_pace', pace_km_per_day: 29.3 } }, t),
    ).toMatchObject({
      title: 'Troca de óleo · CG 160',
      subtitle: 'Estimativa pelo ritmo de 29 km/dia',
    })
    expect(
      describeUpcoming({ ...base, data: { basis: 'date', interval_months: 12 } }, t)?.subtitle,
    ).toBe('Vence por data (12 meses)')
    expect(describeUpcoming({ ...base, kind: 'other' }, t)).toBeNull()
  })

  it('describes km, fueling and maintenance activity', () => {
    const at = new Date().toISOString()
    const km = describeActivity(
      {
        module: 'garage',
        kind: 'garage.odometer',
        occurred_at: at,
        subject: 'CG',
        data: { km: 18420 },
      },
      t,
    )
    expect(km).toMatchObject({ title: 'Km atualizado · CG', value: '18.420 km', icon: 'gauge' })
    const fueling = describeActivity(
      {
        module: 'garage',
        kind: 'garage.fueling',
        occurred_at: at,
        subject: 'CG',
        data: { volume_ml: 7300, total_cents: 4636 },
      },
      t,
    )
    expect(fueling?.subtitle).toContain('7,30 L')
    expect(fueling?.value).toBe('R$ 46,36')
    const oil = describeActivity(
      {
        module: 'garage',
        kind: 'garage.maintenance',
        occurred_at: at,
        subject: 'CG',
        entity_id: '019a0000-0000-7000-8000-000000000000',
        data: { maintenance_kind: 'oil_change', vehicle_id: 'v1', total_cents: 5390 },
      },
      t,
    )
    expect(oil).toMatchObject({ title: 'Troca de óleo · CG', icon: 'droplet' })
  })
})
