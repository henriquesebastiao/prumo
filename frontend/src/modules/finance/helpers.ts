/** Presentation helpers of the finance module: colors, icons, signs and months. */
import type { Translate } from '@/app/registry'
import { calendarDay, money, type SignDisplay } from '@/lib/format'
import type { IconName, Tone } from '@/ui'

import type { AccountKind, Transaction, TransactionKind } from './api'

/** The palette of the API (`color` of accounts, categories and cards). */
export const COLORS = [
  'green',
  'teal',
  'cyan',
  'blue',
  'indigo',
  'violet',
  'pink',
  'red',
  'orange',
  'amber',
  'gray',
] as const
export type FinanceColor = (typeof COLORS)[number]

export function colorTone(color: string): Tone {
  return `swatch-${color}`
}

/** Colors offered by the pickers (design v1); others from the API stay selectable when in use. */
const PICKER_COLORS: FinanceColor[] = ['blue', 'violet', 'orange', 'green', 'pink', 'cyan', 'gray']

export function swatchOptions(t: Translate, current?: string) {
  const values = [...PICKER_COLORS]
  const known = COLORS.find((color) => color === current)
  if (known && !values.includes(known)) values.push(known)
  return values.map((value) => ({
    value,
    label: t(`finance.colors.${value}`),
    color: `var(--color-swatch-${value})`,
  }))
}

/** Icon names stored by the API (Lucide names) → icons of the interface. */
const ICONS: Record<string, IconName> = {
  landmark: 'bank',
  vault: 'vault',
  wallet: 'wallet',
  'trending-up': 'trending-up',
  'credit-card': 'card',
  'piggy-bank': 'piggy-bank',
  utensils: 'utensils',
  house: 'home',
  bus: 'bus',
  car: 'car',
  fuel: 'fuel',
  'heart-pulse': 'heart-pulse',
  'graduation-cap': 'graduation-cap',
  ticket: 'ticket',
  'shopping-bag': 'shopping-bag',
  repeat: 'repeat',
  tag: 'tag',
  briefcase: 'briefcase',
  'code-xml': 'code',
  wrench: 'wrench',
  'paw-print': 'paw-print',
  gift: 'gift',
  plane: 'plane',
  shirt: 'shirt',
  banknote: 'banknote',
  receipt: 'receipt',
  key: 'key',
  building: 'building',
  zap: 'zap',
  droplet: 'droplet',
  flame: 'flame',
  wifi: 'wifi',
  smartphone: 'smartphone',
  tv: 'tv',
  sofa: 'sofa',
  hammer: 'hammer',
  'spray-can': 'spray-can',
  'washing-machine': 'washing-machine',
  'shopping-cart': 'shopping-cart',
  coffee: 'coffee',
  pizza: 'pizza',
  croissant: 'croissant',
  apple: 'apple',
  beer: 'beer',
  'ice-cream-cone': 'ice-cream-cone',
  cake: 'cake',
  'train-front': 'train',
  'car-taxi-front': 'taxi',
  bike: 'bike',
  'square-parking': 'parking',
  map: 'map',
  pill: 'pill',
  stethoscope: 'stethoscope',
  toothbrush: 'toothbrush',
  dumbbell: 'dumbbell',
  brain: 'brain',
  scissors: 'scissors',
  sparkles: 'sparkles',
  glasses: 'glasses',
  film: 'film',
  music: 'music',
  'gamepad-2': 'gamepad',
  book: 'book',
  'party-popper': 'party-popper',
  trophy: 'trophy',
  tent: 'tent',
  'tree-palm': 'palm',
  camera: 'camera',
  palette: 'palette',
  gem: 'gem',
  baby: 'baby',
  users: 'users',
  'heart-handshake': 'heart-handshake',
  church: 'church',
  laptop: 'laptop',
  'book-open': 'book-open',
  coins: 'coins',
  scale: 'scale',
  percent: 'percent',
  shield: 'shield',
  'file-text': 'page',
  store: 'store',
  package: 'package',
}

/** Unknown names (created by another client) fall back to a generic icon (D33). */
export function dataIcon(name: string | null | undefined, fallback: IconName = 'tag'): IconName {
  return (name && ICONS[name]) || fallback
}

export const ACCOUNT_ICONS = ['landmark', 'vault', 'wallet', 'trending-up', 'credit-card']
/** The category icons, by group (the Android app shows the same groups; D45). */
export const CATEGORY_ICONS = [
  // Casa
  'house',
  'key',
  'building',
  'zap',
  'droplet',
  'flame',
  'wifi',
  'smartphone',
  'tv',
  'sofa',
  'hammer',
  'spray-can',
  'washing-machine',
  // Alimentação
  'utensils',
  'shopping-cart',
  'coffee',
  'pizza',
  'croissant',
  'apple',
  'beer',
  'ice-cream-cone',
  'cake',
  // Transporte
  'car',
  'fuel',
  'bus',
  'train-front',
  'car-taxi-front',
  'bike',
  'square-parking',
  'wrench',
  'plane',
  'map',
  // Saúde e cuidado
  'heart-pulse',
  'pill',
  'stethoscope',
  'toothbrush',
  'dumbbell',
  'brain',
  'scissors',
  'sparkles',
  'glasses',
  // Lazer
  'ticket',
  'film',
  'music',
  'gamepad-2',
  'book',
  'party-popper',
  'trophy',
  'tent',
  'tree-palm',
  'camera',
  'palette',
  // Pessoal e família
  'shirt',
  'gem',
  'baby',
  'users',
  'paw-print',
  'gift',
  'heart-handshake',
  'church',
  // Trabalho e estudo
  'briefcase',
  'laptop',
  'code-xml',
  'graduation-cap',
  'book-open',
  // Dinheiro e contas
  'banknote',
  'trending-up',
  'piggy-bank',
  'coins',
  'receipt',
  'credit-card',
  'repeat',
  'scale',
  'percent',
  'shield',
  'file-text',
  'shopping-bag',
  'store',
  'package',
  'tag',
]

export function iconOptions(names: string[], t: Translate, current?: string) {
  const values = current && !names.includes(current) ? [...names, current] : names
  return values.map((value) => ({
    value,
    icon: dataIcon(value),
    label: t(`finance.icons.${value}`),
  }))
}

export const ACCOUNT_KINDS: AccountKind[] = ['checking', 'savings', 'cash', 'investment', 'other']

/** How the amount of each kind reads in lists: `+ R$` income, `− R$` expense, plain transfer. */
const SIGNS: Record<TransactionKind, { factor: number; display: SignDisplay }> = {
  income: { factor: 1, display: 'always' },
  expense: { factor: -1, display: 'negative' },
  transfer: { factor: 1, display: 'never' },
  card_payment: { factor: -1, display: 'negative' },
  adjustment: { factor: 1, display: 'always' },
}

export function signedAmount(kind: TransactionKind, cents: number): string {
  const sign = SIGNS[kind]
  return money(sign.factor * cents, sign.display)
}

export function amountTone(kind: TransactionKind, cents: number): 'success' | 'default' {
  return (kind === 'income' || (kind === 'adjustment' && cents > 0)) && cents !== 0
    ? 'success'
    : 'default'
}

export function transactionIcon(transaction: Transaction): IconName {
  switch (transaction.kind) {
    case 'transfer':
      return 'transfer'
    case 'card_payment':
      return 'card'
    case 'adjustment':
      return 'sliders'
    default:
      return dataIcon(transaction.category?.icon)
  }
}

/** Description, or the kind's label when the API keeps it empty (F16). */
export function transactionTitle(transaction: Transaction, t: Translate): string {
  return transaction.description || t(`finance.kinds.${transaction.kind}`)
}

// ---------------------------------------------------------------- months

/** `YYYY-MM` of today in the user's time zone. */
export function currentMonth(): string {
  return calendarDay(new Date()).slice(0, 7)
}

export function today(): string {
  return calendarDay(new Date())
}

/** First and last day of a `YYYY-MM` month. */
export function monthRange(month: string): { from: string; to: string } {
  const [year, index] = month.split('-').map(Number) as [number, number]
  const last = new Date(Date.UTC(year, index, 0)).getUTCDate()
  return { from: `${month}-01`, to: `${month}-${String(last).padStart(2, '0')}` }
}

export function shiftMonth(month: string, delta: number): string {
  const [year, index] = month.split('-').map(Number) as [number, number]
  const date = new Date(Date.UTC(year, index - 1 + delta, 1))
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`
}
