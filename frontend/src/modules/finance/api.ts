/** Queries and mutations of the finance module (TanStack Query). Keys start with `finance`. */
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import { api, unwrap, type Schemas } from '@/lib/api/client'

export type Account = Schemas['AccountRead']
export type Category = Schemas['CategoryRead']
export type CreditCard = Schemas['CreditCardRead']
export type Invoice = Schemas['InvoiceRead']
export type InvoiceDetail = Schemas['InvoiceDetail']
export type Transaction = Schemas['TransactionRead']
export type TransactionKind = Schemas['TransactionKind']
export type CategoryKind = Schemas['CategoryKind']
export type AccountKind = Schemas['AccountKind']
export type Overview = Schemas['FinanceOverview']
export type FinanceSummary = Schemas['FinanceSummary']
export type OpenInvoice = Schemas['OpenInvoice']
export type CategoryShare = Schemas['CategoryShare']

export interface TransactionFilters {
  from?: string
  to?: string
  kind?: TransactionKind
  account_id?: string
  credit_card_id?: string
  category_id?: string
  q?: string
}

const PAGE = 50

export const financeKeys = {
  all: ['finance'] as const,
  overview: (month: string) => ['finance', 'overview', month] as const,
  accounts: (archived: string) => ['finance', 'accounts', archived] as const,
  categories: (month: string, archived: string) =>
    ['finance', 'categories', month, archived] as const,
  cards: (archived: string) => ['finance', 'cards', archived] as const,
  invoices: (cardId: string) => ['finance', 'card', cardId, 'invoices'] as const,
  invoice: (cardId: string, closingOn: string) =>
    ['finance', 'card', cardId, 'invoice', closingOn] as const,
  transactions: (filters: object) => ['finance', 'transactions', filters] as const,
}

/** Every finance mutation changes balances, totals, invoices and Início. */
function useInvalidateFinance() {
  const client = useQueryClient()
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: financeKeys.all }),
      client.invalidateQueries({ queryKey: ['dashboard'] }),
    ])
}

// ---------------------------------------------------------------- reads

export function useOverview(month: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => financeKeys.overview(toValue(month))),
    queryFn: () =>
      unwrap(api.GET('/api/v1/finance/overview', { params: { query: { month: toValue(month) } } })),
  })
}

export function useAccounts(archived: 'false' | 'true' | 'all' = 'false') {
  return useQuery({
    queryKey: financeKeys.accounts(archived),
    queryFn: () => unwrap(api.GET('/api/v1/finance/accounts', { params: { query: { archived } } })),
  })
}

export function useCategories(
  month: MaybeRefOrGetter<string | undefined> = undefined,
  archived: 'false' | 'true' | 'all' = 'false',
) {
  return useQuery({
    queryKey: computed(() => financeKeys.categories(toValue(month) ?? 'current', archived)),
    queryFn: () => {
      const value = toValue(month)
      return unwrap(
        api.GET('/api/v1/finance/categories', {
          params: { query: value ? { month: value, archived } : { archived } },
        }),
      )
    },
  })
}

export function useCards(archived: 'false' | 'true' | 'all' = 'false') {
  return useQuery({
    queryKey: financeKeys.cards(archived),
    queryFn: () =>
      unwrap(api.GET('/api/v1/finance/credit-cards', { params: { query: { archived } } })),
    select: (list) => list.items,
  })
}

export function useInvoices(cardId: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => financeKeys.invoices(toValue(cardId))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/finance/credit-cards/{card_id}/invoices', {
          params: { path: { card_id: toValue(cardId) } },
        }),
      ),
    select: (list) => list.items,
    enabled: computed(() => Boolean(toValue(cardId))),
  })
}

export function useInvoice(cardId: MaybeRefOrGetter<string>, closingOn: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => financeKeys.invoice(toValue(cardId), toValue(closingOn))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/finance/credit-cards/{card_id}/invoices/{closing_on}', {
          params: { path: { card_id: toValue(cardId), closing_on: toValue(closingOn) } },
        }),
      ),
    enabled: computed(() => Boolean(toValue(cardId) && toValue(closingOn))),
  })
}

export function useTransactions(filters: MaybeRefOrGetter<TransactionFilters>, pageSize = PAGE) {
  return useInfiniteQuery({
    queryKey: computed(() => financeKeys.transactions({ ...toValue(filters), pageSize })),
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      unwrap(
        api.GET('/api/v1/finance/transactions', {
          params: { query: { ...toValue(filters), limit: pageSize, offset: pageParam } },
        }),
      ),
    getNextPageParam: (last) =>
      last.offset + last.items.length < last.total ? last.offset + last.items.length : undefined,
  })
}

// ---------------------------------------------------------------- transactions

export function useSaveTransaction() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['TransactionCreate'] | Schemas['TransactionUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/finance/transactions/{transaction_id}', {
              params: { path: { transaction_id: id } },
              body: body as Schemas['TransactionUpdate'],
            }),
          )
        : unwrap(
            api.POST('/api/v1/finance/transactions', {
              body: body as Schemas['TransactionCreate'],
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteTransaction() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({ id, all = false }: { id: string; all?: boolean }) =>
      unwrap(
        api.DELETE('/api/v1/finance/transactions/{transaction_id}', {
          params: { path: { transaction_id: id }, query: { installments: all ? 'all' : 'one' } },
        }),
      ),
    onSuccess: invalidate,
  })
}

// ---------------------------------------------------------------- accounts

export function useSaveAccount() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['AccountCreate'] | Schemas['AccountUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/finance/accounts/{account_id}', {
              params: { path: { account_id: id } },
              body: body as Schemas['AccountUpdate'],
            }),
          )
        : unwrap(api.POST('/api/v1/finance/accounts', { body: body as Schemas['AccountCreate'] })),
    onSuccess: invalidate,
  })
}

export function useArchiveAccount() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({ id, archived }: { id: string; archived: boolean }) =>
      archived
        ? unwrap(
            api.POST('/api/v1/finance/accounts/{account_id}/archive', {
              params: { path: { account_id: id } },
            }),
          )
        : unwrap(
            api.POST('/api/v1/finance/accounts/{account_id}/unarchive', {
              params: { path: { account_id: id } },
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteAccount() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/finance/accounts/{account_id}', {
          params: { path: { account_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useAdjustBalance() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Schemas['AdjustmentCreate'] }) =>
      unwrap(
        api.POST('/api/v1/finance/accounts/{account_id}/adjustments', {
          params: { path: { account_id: id } },
          body,
        }),
      ),
    onSuccess: invalidate,
  })
}

// ---------------------------------------------------------------- categories

export function useSaveCategory() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['CategoryCreate'] | Schemas['CategoryUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/finance/categories/{category_id}', {
              params: { path: { category_id: id } },
              body: body as Schemas['CategoryUpdate'],
            }),
          )
        : unwrap(
            api.POST('/api/v1/finance/categories', { body: body as Schemas['CategoryCreate'] }),
          ),
    onSuccess: invalidate,
  })
}

export function useArchiveCategory() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({ id, archived }: { id: string; archived: boolean }) =>
      archived
        ? unwrap(
            api.POST('/api/v1/finance/categories/{category_id}/archive', {
              params: { path: { category_id: id } },
            }),
          )
        : unwrap(
            api.POST('/api/v1/finance/categories/{category_id}/unarchive', {
              params: { path: { category_id: id } },
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteCategory() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/finance/categories/{category_id}', {
          params: { path: { category_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

// ---------------------------------------------------------------- cards and invoices

export function useSaveCard() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['CreditCardCreate'] | Schemas['CreditCardUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/finance/credit-cards/{card_id}', {
              params: { path: { card_id: id } },
              body: body as Schemas['CreditCardUpdate'],
            }),
          )
        : unwrap(
            api.POST('/api/v1/finance/credit-cards', {
              body: body as Schemas['CreditCardCreate'],
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useArchiveCard() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({ id, archived }: { id: string; archived: boolean }) =>
      archived
        ? unwrap(
            api.POST('/api/v1/finance/credit-cards/{card_id}/archive', {
              params: { path: { card_id: id } },
            }),
          )
        : unwrap(
            api.POST('/api/v1/finance/credit-cards/{card_id}/unarchive', {
              params: { path: { card_id: id } },
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteCard() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/finance/credit-cards/{card_id}', {
          params: { path: { card_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function usePayInvoice() {
  const invalidate = useInvalidateFinance()
  return useMutation({
    mutationFn: ({
      cardId,
      closingOn,
      body,
    }: {
      cardId: string
      closingOn: string
      body: Schemas['InvoicePaymentCreate']
    }) =>
      unwrap(
        api.POST('/api/v1/finance/credit-cards/{card_id}/invoices/{closing_on}/payments', {
          params: { path: { card_id: cardId, closing_on: closingOn } },
          body,
        }),
      ),
    onSuccess: invalidate,
  })
}
