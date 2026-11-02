import type { RouteLocationRaw } from 'vue-router'

import type { IconName } from './icons'

/**
 * A tone colors a component: a module id (`finance`, `garage`, `reading`…) or a status.
 * It becomes `data-tone` on the element; src/design/tones.css maps it to colors.
 */
export type StatusTone = 'neutral' | 'accent' | 'danger' | 'success' | 'warning'
export type Tone = StatusTone | (string & {})

export interface Option<V extends string = string> {
  value: V
  label: string
  description?: string
}

export interface TabItem<V extends string = string> {
  value: V
  label: string
  count?: number
  to?: RouteLocationRaw
}

export type MenuEntry =
  | { type: 'separator' }
  | { type: 'label'; label: string }
  | {
      type?: 'item'
      label: string
      icon?: IconName
      tone?: Tone
      shortcut?: string
      danger?: boolean
      /** Shows a check mark (current choice, such as the theme). */
      checked?: boolean
      to?: RouteLocationRaw
      onSelect?: () => void
    }

export interface ChartDatum {
  label: string
  value?: number
  /** Grouped bars: one value per series. */
  values?: number[]
  highlight?: boolean
}
