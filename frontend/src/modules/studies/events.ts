/** How the studies items of "Atividade recente" appear on Início (E11). */
import type { EventView, Translate } from '@/app/registry'
import type { Schemas } from '@/lib/api/client'
import { relativeDateTime } from '@/lib/format'

import { minutes } from './helpers'

type Data = Record<string, string | number | boolean | null | undefined>

export function describeActivity(item: Schemas['ActivityItem'], t: Translate): EventView | null {
  if (item.kind !== 'studies.session') return null
  const data = (item.data ?? {}) as Data
  const when = relativeDateTime(item.occurred_at)
  const topic = typeof data.topic === 'string' && data.topic ? ` · ${data.topic}` : ''
  return {
    title: t('studies.events.session', { subject: item.subject }),
    subtitle: `${when}${topic}`,
    value: typeof data.duration_minutes === 'number' ? minutes(data.duration_minutes) : undefined,
    icon: 'graduation-cap',
    to: item.entity_id
      ? { name: 'studies.subject', params: { subjectId: item.entity_id } }
      : undefined,
  }
}
