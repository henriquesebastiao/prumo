import { QueryClient } from '@tanstack/vue-query'

import { isApiError } from '@/lib/api/errors'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // Client errors (4xx) are final; retry only network and server failures.
      retry: (failureCount, error) =>
        failureCount < 2 && (!isApiError(error) || error.status === 0 || error.status >= 500),
    },
    mutations: { retry: false },
  },
})
