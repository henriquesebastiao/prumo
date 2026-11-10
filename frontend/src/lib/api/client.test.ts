import { describe, expect, it, vi } from 'vitest'

import { createApiClient, onUnauthorized, unwrap } from './client'
import { ApiError } from './errors'

function json(status: number, body: unknown): Response {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function clientReturning(response: Response) {
  const fetchMock = vi.fn<typeof fetch>(async () => response)
  return { client: createApiClient(fetchMock), fetchMock }
}

describe('api client', () => {
  it('returns data on success', async () => {
    const { client } = clientReturning(
      json(200, { status: 'ok', database: 'ok', version: '0.2.0' }),
    )
    await expect(unwrap(client.GET('/api/health'))).resolves.toMatchObject({ status: 'ok' })
  })

  it('sends X-Prumo-Client only on mutations', async () => {
    const { client, fetchMock } = clientReturning(json(204, undefined))
    await unwrap(client.POST('/api/v1/auth/logout'))
    await unwrap(client.GET('/api/v1/me')).catch(() => undefined)
    const [logout, me] = fetchMock.mock.calls.map(([request]) => request as Request)
    expect(logout?.headers.get('X-Prumo-Client')).toBe('web')
    expect(me?.headers.get('X-Prumo-Client')).toBeNull()
  })

  it('throws ApiError with code and fields', async () => {
    const { client } = clientReturning(
      json(422, {
        error: {
          code: 'validation_error',
          message: 'Invalid request.',
          fields: [{ path: 'display_name', code: 'string_too_short', message: '…' }],
        },
      }),
    )
    const error = await unwrap(client.PATCH('/api/v1/me', { body: { display_name: '' } })).catch(
      (e: unknown) => e,
    )
    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).code).toBe('validation_error')
    expect((error as ApiError).fieldErrors()['display_name']?.code).toBe('string_too_short')
  })

  it('notifies listeners on 401', async () => {
    const listener = vi.fn()
    const stop = onUnauthorized(listener)
    const { client } = clientReturning(
      json(401, { error: { code: 'auth.session_expired', message: 'Session expired.' } }),
    )
    await expect(unwrap(client.GET('/api/v1/me'))).rejects.toMatchObject({
      status: 401,
      code: 'auth.session_expired',
    })
    expect(listener).toHaveBeenCalledOnce()
    stop()
  })

  it('maps network failures to network_error', async () => {
    const client = createApiClient(vi.fn<typeof fetch>(async () => Promise.reject(new TypeError())))
    await expect(unwrap(client.GET('/api/health'))).rejects.toMatchObject({
      status: 0,
      code: 'network_error',
    })
  })
})
