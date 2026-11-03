import { describe, expect, it, vi } from 'vitest'

import { createApiClient } from '@/lib/api/client'

import { coverUrl, uploadCover } from './api'

describe('reading api', () => {
  it('uploads the cover as multipart with the client header', async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async () =>
        new Response(JSON.stringify({ id: 'b1', has_cover: true }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
    )
    await uploadCover(createApiClient(fetchMock), 'b1', new Blob(['png'], { type: 'image/png' }))
    const request = fetchMock.mock.calls[0]![0] as Request
    expect(request.method).toBe('PUT')
    expect(new URL(request.url).pathname).toBe('/api/v1/reading/books/b1/cover')
    expect(request.headers.get('Content-Type')).toMatch(/^multipart\/form-data; boundary=/)
    expect(request.headers.get('X-Prumo-Client')).toBe('web')
  })

  it('versions the cover URL', () => {
    expect(coverUrl({ id: 'b1', has_cover: false })).toBeUndefined()
    expect(coverUrl({ id: 'b1', has_cover: true, cover_updated_at: '2026-11-17T10:00:00Z' })).toBe(
      '/api/v1/reading/books/b1/cover?v=2026-11-17T10%3A00%3A00Z',
    )
  })
})
