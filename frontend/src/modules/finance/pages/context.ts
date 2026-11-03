import { inject, provide, type InjectionKey, type Ref } from 'vue'

/** State shared by the Finanças page and its tabs. */
export interface FinanceContext {
  /** Month in view (`YYYY-MM`), kept in the `mes` query parameter. */
  month: Ref<string>
  /** Increments when the header's "Nova conta/categoria" is clicked; the tab opens its form. */
  createRequests: Ref<number>
  newTransaction: (kind?: 'expense' | 'income' | 'transfer') => void
}

const KEY: InjectionKey<FinanceContext> = Symbol('finance')

export function provideFinance(context: FinanceContext): void {
  provide(KEY, context)
}

export function useFinance(): FinanceContext {
  const context = inject(KEY)
  if (!context) throw new Error('useFinance() outside FinancePage')
  return context
}
