import { inject, provide, type InjectionKey, type Ref } from 'vue'

/** State shared by the Livros page and its tabs. */
export interface ReadingContext {
  /** Search of the header (debounced): title or author on the shelf, text in the notes. */
  query: Ref<string>
  /** Ownership filter of the shelf ("Tenho / Não tenho"). */
  owned: Ref<'all' | 'yes' | 'no'>
}

const KEY: InjectionKey<ReadingContext> = Symbol('reading')

export function provideReading(context: ReadingContext): void {
  provide(KEY, context)
}

export function useReading(): ReadingContext {
  const context = inject(KEY)
  if (!context) throw new Error('useReading() outside ReadingPage')
  return context
}
