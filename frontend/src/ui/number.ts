import { decimal, integer } from '@/lib/format'

/** Parses user input in pt-BR notation: `18.300` → 18300, `58,42` → 58.42. */
export function parseLocaleNumber(text: string): number | null {
  const cleaned = text.replace(/\s/g, '').replace(/\./g, '').replace(',', '.')
  if (cleaned === '' || cleaned === '-') return null
  const value = Number(cleaned)
  return Number.isFinite(value) ? value : null
}

export function formatLocaleNumber(value: number | null, decimals: number): string {
  if (value === null) return ''
  return decimals === 0 ? integer(value) : decimal(value, decimals)
}
