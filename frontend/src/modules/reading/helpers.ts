/** Presentation helpers of the reading module. */
import type { BookStatus } from './api'

/** Drawn covers follow the status, as on the boards: tone while reading, paper in the queue,
 * ink once read. */
const VARIANTS = { reading: 'tone', want_to_read: 'paper', read: 'ink' } as const
export type CoverVariant = (typeof VARIANTS)[BookStatus]

export function coverVariant(status: BookStatus): CoverVariant {
  return VARIANTS[status]
}

export const STATUSES: BookStatus[] = ['want_to_read', 'reading', 'read']
