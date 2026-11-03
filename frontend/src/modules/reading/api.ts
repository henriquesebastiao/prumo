/** Queries and mutations of the reading module (TanStack Query). Keys start with `reading`. */
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import { api, unwrap, type Schemas } from '@/lib/api/client'

export type Book = Schemas['BookRead']
export type BookDetail = Schemas['BookDetail']
export type BookStatus = Schemas['BookStatus']
export type Note = Schemas['NoteRead']
export type ReadingSummary = Schemas['ReadingSummary']

const ALL = 200
const PAGE = 30

export const readingKeys = {
  all: ['reading'] as const,
  overview: ['reading', 'overview'] as const,
  books: (filters: object) => ['reading', 'books', filters] as const,
  book: (id: string) => ['reading', 'book', id] as const,
  notes: (bookId: string) => ['reading', 'book', bookId, 'notes'] as const,
  allNotes: (q: string) => ['reading', 'notes', q] as const,
}

/** Every reading mutation changes derived values (progress, pace, counts) and Início. */
function useInvalidateReading() {
  const client = useQueryClient()
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: readingKeys.all }),
      client.invalidateQueries({ queryKey: ['dashboard'] }),
    ])
}

/** URL of the cover image; the version makes the browser fetch a new one after a change. */
export function coverUrl(book: {
  id: string
  has_cover: boolean
  cover_updated_at?: string | null
}) {
  if (!book.has_cover) return undefined
  const version = book.cover_updated_at ? `?v=${encodeURIComponent(book.cover_updated_at)}` : ''
  return `/api/v1/reading/books/${book.id}/cover${version}`
}

// ---------------------------------------------------------------- reads

export function useOverview() {
  return useQuery({
    queryKey: readingKeys.overview,
    queryFn: () => unwrap(api.GET('/api/v1/reading/overview')),
  })
}

export interface BookFilters {
  q?: string
  owned?: boolean
  status?: BookStatus
}

export function useBooks(filters: MaybeRefOrGetter<BookFilters> = {}) {
  return useQuery({
    queryKey: computed(() => readingKeys.books(toValue(filters))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/reading/books', {
          params: { query: { ...toValue(filters), limit: ALL } },
        }),
      ),
    select: (page) => page.items,
  })
}

export function useBook(id: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => readingKeys.book(toValue(id))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/reading/books/{book_id}', {
          params: { path: { book_id: toValue(id) } },
        }),
      ),
  })
}

export function useBookNotes(id: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => readingKeys.notes(toValue(id))),
    queryFn: () =>
      unwrap(
        api.GET('/api/v1/reading/books/{book_id}/notes', {
          params: { path: { book_id: toValue(id) } },
        }),
      ),
    select: (list) => list.items,
  })
}

export function useAllNotes(q: MaybeRefOrGetter<string>) {
  return useInfiniteQuery({
    queryKey: computed(() => readingKeys.allNotes(toValue(q))),
    initialPageParam: 0,
    queryFn: ({ pageParam }) => {
      const text = toValue(q)
      return unwrap(
        api.GET('/api/v1/reading/notes', {
          params: { query: { ...(text ? { q: text } : {}), limit: PAGE, offset: pageParam } },
        }),
      )
    },
    getNextPageParam: (last) =>
      last.offset + last.items.length < last.total ? last.offset + last.items.length : undefined,
  })
}

// ---------------------------------------------------------------- mutations

export function useSaveBook() {
  const invalidate = useInvalidateReading()
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id?: string
      body: Schemas['BookCreate'] | Schemas['BookUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/reading/books/{book_id}', {
              params: { path: { book_id: id } },
              body: body as Schemas['BookUpdate'],
            }),
          )
        : unwrap(api.POST('/api/v1/reading/books', { body: body as Schemas['BookCreate'] })),
    onSuccess: invalidate,
  })
}

export function useDeleteBook() {
  const invalidate = useInvalidateReading()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE('/api/v1/reading/books/{book_id}', { params: { path: { book_id: id } } })),
    onSuccess: invalidate,
  })
}

export function useSaveProgress() {
  const invalidate = useInvalidateReading()
  return useMutation({
    mutationFn: ({ id, page }: { id: string; page: number }) =>
      unwrap(
        api.POST('/api/v1/reading/books/{book_id}/progress', {
          params: { path: { book_id: id } },
          body: { page },
        }),
      ),
    onSuccess: invalidate,
  })
}

/** Sends a cover as `multipart/form-data` (the browser sets the boundary). */
export function uploadCover(client: typeof api, id: string, file: Blob) {
  const form = new FormData()
  form.append('file', file)
  return unwrap(
    client.PUT('/api/v1/reading/books/{book_id}/cover', {
      params: { path: { book_id: id } },
      body: form as unknown as Schemas['Body_reading_set_cover'],
      bodySerializer: (body) => body as unknown as FormData,
    }),
  )
}

export function useSetCover() {
  const invalidate = useInvalidateReading()
  return useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => uploadCover(api, id, file),
    onSuccess: invalidate,
  })
}

export function useRemoveCover() {
  const invalidate = useInvalidateReading()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.DELETE('/api/v1/reading/books/{book_id}/cover', {
          params: { path: { book_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useSaveNote() {
  const invalidate = useInvalidateReading()
  return useMutation({
    mutationFn: ({
      bookId,
      id,
      body,
    }: {
      bookId: string
      id?: string
      body: Schemas['NoteCreate'] | Schemas['NoteUpdate']
    }) =>
      id
        ? unwrap(
            api.PATCH('/api/v1/reading/books/{book_id}/notes/{note_id}', {
              params: { path: { book_id: bookId, note_id: id } },
              body: body as Schemas['NoteUpdate'],
            }),
          )
        : unwrap(
            api.POST('/api/v1/reading/books/{book_id}/notes', {
              params: { path: { book_id: bookId } },
              body: body as Schemas['NoteCreate'],
            }),
          ),
    onSuccess: invalidate,
  })
}

export function useDeleteNote() {
  const invalidate = useInvalidateReading()
  return useMutation({
    mutationFn: ({ bookId, id }: { bookId: string; id: string }) =>
      unwrap(
        api.DELETE('/api/v1/reading/books/{book_id}/notes/{note_id}', {
          params: { path: { book_id: bookId, note_id: id } },
        }),
      ),
    onSuccess: invalidate,
  })
}
