/** How the reading items of "Atividade recente" appear on Início. */
import type { EventView, Translate } from '@/app/registry'
import type { Schemas } from '@/lib/api/client'
import { relativeDateTime } from '@/lib/format'

type Data = Record<string, string | number | boolean | null | undefined>

export function describeActivity(item: Schemas['ActivityItem'], t: Translate): EventView | null {
  const data = (item.data ?? {}) as Data
  const when = relativeDateTime(item.occurred_at)
  const to = item.entity_id
    ? { name: 'reading.book', params: { bookId: item.entity_id } }
    : undefined
  const title = { title: item.subject }
  if (item.kind === 'reading.progress') {
    const pages = typeof data.pages === 'number' ? data.pages : 0
    const finished = data.page === data.total_pages && data.status === 'read'
    return {
      title: t(finished ? 'reading.events.finished' : 'reading.events.progress', title),
      subtitle: `${when} · ${t('reading.events.untilPage', { page: data.page ?? 0 })}`,
      value: pages > 0 ? t('reading.events.pages', { n: pages }) : undefined,
      icon: 'bookmark',
      to,
    }
  }
  if (item.kind === 'reading.note') {
    return {
      title: t('reading.events.note', title),
      subtitle: typeof data.excerpt === 'string' ? `${when} · ${data.excerpt}` : when,
      icon: 'note',
      to,
    }
  }
  return null
}
