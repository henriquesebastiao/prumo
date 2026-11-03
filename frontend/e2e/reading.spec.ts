import { expect, test, type Page } from '@playwright/test'

import { DESIGN_NOW, settle } from './fixtures'

/** Livros screens against the seeded API (backend/scripts/e2e_server.py). */
const OUT = 'e2e/output'

test.describe.configure({ mode: 'serial' })

async function signIn(page: Page, theme: 'light' | 'dark' = 'light') {
  await page.clock.setFixedTime(DESIGN_NOW)
  await page.emulateMedia({ colorScheme: theme })
  await page.addInitScript(() => localStorage.setItem('prumo.theme', 'system'))
  const response = await page.request.post('/api/v1/auth/login', {
    data: { username: 'henrique', password: 'prumo-demo-01', client: 'web' },
  })
  expect(response.ok()).toBeTruthy()
}

async function bookId(page: Page, title: string): Promise<string> {
  const response = await page.request.get('/api/v1/reading/books')
  const body = (await response.json()) as { items: { id: string; title: string }[] }
  return body.items.find((book) => book.title === title)!.id
}

for (const theme of ['light', 'dark'] as const) {
  test(`shelf ${theme}`, async ({ page }) => {
    await signIn(page, theme)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/livros')
    await expect(page.getByText('Lendo agora')).toBeVisible()
    await expect(page.getByText('O Hobbit').first()).toBeVisible()
    await settle(page)
    await page.screenshot({ path: `${OUT}/reading-shelf-${theme}.png` })
  })
}

test('book detail', async ({ page }) => {
  await signIn(page)
  const id = await bookId(page, 'Código Limpo')
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto(`/livros/${id}`)
  await expect(page.getByText('Ritmo de leitura')).toBeVisible()
  await expect(page.getByText('Funções pequenas', { exact: false })).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/reading-detail.png` })
})

test('add book dialog', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1280, height: 800 })
  await page.goto('/livros')
  await expect(page.getByText('Lendo agora')).toBeVisible()
  await page.getByRole('button', { name: 'Adicionar livro' }).first().click()
  await expect(page.locator('.p-dialog--modal')).toBeVisible()
  await page.getByRole('textbox', { name: 'Título' }).fill('O Hobbit')
  await page.getByRole('textbox', { name: 'Autor' }).fill('J.R.R. Tolkien')
  await page.getByRole('textbox', { name: 'Número de páginas' }).fill('336')
  await page.getByRole('textbox', { name: 'Título' }).focus()
  await settle(page)
  await page.screenshot({ path: `${OUT}/reading-dialog-book.png` })
})

test('note dialog', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1280, height: 760 })
  await page.goto('/')
  await expect(page.getByText('Lendo agora')).toBeVisible()
  await page.keyboard.press('n')
  await expect(page.getByRole('listbox')).toBeFocused()
  await page.keyboard.press('L')
  await expect(page.locator('.p-dialog--modal')).toBeVisible()
  await expect(page.locator('.p-popover')).toHaveCount(0)
  await page.keyboard.type(
    'Comentário bom é o que explica o porquê, não o quê. Revisar os comentários antigos do projeto e apagar os que só repetem o código.',
  )
  await settle(page)
  await page.screenshot({ path: `${OUT}/reading-dialog-note.png` })
})

test('home with every module', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 1440, height: 1160 })
  await page.goto('/')
  await expect(page.getByText('Lendo agora')).toBeVisible()
  await settle(page)
  await page.screenshot({ path: `${OUT}/reading-home-light.png` })
})
