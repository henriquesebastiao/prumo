import { expect, test, type Page } from '@playwright/test'

import { DESIGN_NOW, settle } from './fixtures'

/** Every module screen on a phone and a tablet: no horizontal scroll, full-page captures. */
const OUT = 'e2e/output/responsive'

const WIDTHS = { phone: 390, tablet: 820 } as const

async function signIn(page: Page) {
  await page.clock.setFixedTime(DESIGN_NOW)
  await page.emulateMedia({ colorScheme: 'light' })
  const response = await page.request.post('/api/v1/auth/login', {
    data: { username: 'henrique', password: 'prumo-demo-01', client: 'web' },
  })
  expect(response.ok()).toBeTruthy()
}

async function firstId(page: Page, path: string, title: string): Promise<string> {
  const body = (await (await page.request.get(path)).json()) as {
    items: { id: string; name?: string; title?: string }[]
  }
  return body.items.find((item) => (item.name ?? item.title) === title)!.id
}

const screens: { name: string; path: string | ((page: Page) => Promise<string>); ready: string }[] =
  [
    { name: 'home', path: '/', ready: 'Lendo agora' },
    { name: 'finance-overview', path: '/financas', ready: 'Saldo por conta' },
    { name: 'finance-transactions', path: '/financas/transacoes', ready: 'Padaria' },
    { name: 'finance-accounts', path: '/financas/contas', ready: 'Suas contas' },
    { name: 'finance-cards', path: '/financas/cartoes', ready: 'Faturas anteriores' },
    { name: 'finance-categories', path: '/financas/categorias', ready: 'Receitas' },
    { name: 'garage-list', path: '/veiculos', ready: 'Fiat Strada Freedom' },
    {
      name: 'garage-detail',
      path: async (page) =>
        `/veiculos/${await firstId(page, '/api/v1/garage/vehicles', 'Honda CG 160 Fan')}`,
      ready: 'Próxima troca de óleo',
    },
    { name: 'reading-shelf', path: '/livros', ready: 'Lendo agora' },
    {
      name: 'reading-detail',
      path: async (page) =>
        `/livros/${await firstId(page, '/api/v1/reading/books', 'Código Limpo')}`,
      ready: 'Ritmo de leitura',
    },
    { name: 'reading-notes', path: '/livros/anotacoes', ready: 'Funções pequenas' },
    { name: 'studies-today', path: '/estudos', ready: 'Em andamento' },
    { name: 'studies-week', path: '/estudos/semana', ready: 'Esta semana' },
    { name: 'studies-subjects', path: '/estudos/materias', ready: 'Estruturas de Dados' },
    { name: 'studies-plan', path: '/estudos/plano', ready: 'Vigente desde' },
    {
      name: 'studies-subject',
      path: async (page) =>
        `/estudos/materias/${await firstId(page, '/api/v1/studies/subjects', 'FastAPI')}`,
      ready: 'Minutos por semana',
    },
    { name: 'settings', path: '/configuracoes', ready: 'Seus dados' },
  ]

for (const [device, width] of Object.entries(WIDTHS)) {
  for (const screen of screens) {
    test(`${screen.name} on ${device}`, async ({ page }) => {
      await signIn(page)
      await page.setViewportSize({ width, height: 900 })
      await page.goto(typeof screen.path === 'string' ? screen.path : await screen.path(page))
      await expect(page.getByText(screen.ready, { exact: false }).first()).toBeVisible()
      await settle(page)
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      )
      expect(overflow, 'horizontal scroll').toBeLessThanOrEqual(0)
      await page.screenshot({ path: `${OUT}/${screen.name}-${device}.png`, fullPage: true })
    })
  }
}

test('transaction dialog on phone', async ({ page }) => {
  await signIn(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/financas')
  await page.getByRole('button', { name: 'Nova transação' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await settle(page)
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  )
  expect(overflow).toBeLessThanOrEqual(0)
  await page.screenshot({ path: `${OUT}/finance-dialog-phone.png` })
})
