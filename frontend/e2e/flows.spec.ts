import { expect, test, type Page } from '@playwright/test'

import { DESIGN_NOW } from './fixtures'

/**
 * Main flows against the real API (backend/scripts/e2e_server.py), with an empty account
 * (`teste`) so the boards data of the screenshots stays untouched.
 */

const USERNAME = 'teste'
const PASSWORD = 'prumo-teste-01'

async function signIn(page: Page) {
  await page.clock.setFixedTime(DESIGN_NOW)
  const response = await page.request.post('/api/v1/auth/login', {
    data: { username: USERNAME, password: PASSWORD, client: 'web' },
  })
  expect(response.ok()).toBeTruthy()
}

async function quickAction(page: Page, key: string) {
  await page.keyboard.press('n')
  await expect(page.getByRole('listbox')).toBeFocused()
  await page.keyboard.press(key)
  await expect(page.getByRole('dialog')).toBeVisible()
}

test.describe.configure({ mode: 'serial' })

test('login, Início and logout', async ({ page }) => {
  await page.clock.setFixedTime(DESIGN_NOW)
  await page.goto('/')
  await expect(page).toHaveURL(/\/entrar/)
  await page.getByLabel('Usuário', { exact: true }).fill(USERNAME)
  await page.getByLabel('Senha', { exact: true }).fill('senha-errada-123')
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByText('Usuário ou senha incorretos.')).toBeVisible()
  await page.getByLabel('Senha', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByRole('heading', { name: /Teste/ })).toBeVisible()
  await expect(page.getByText('Cadastre uma conta para ver o resumo do mês.')).toBeVisible()

  await page.getByRole('button', { name: 'Conta' }).click()
  await page.getByRole('menuitem', { name: 'Sair' }).click()
  await expect(page).toHaveURL(/\/entrar/)
})

test('finance: account, expense and balance', async ({ page }) => {
  await signIn(page)
  await page.goto('/financas/contas')
  await page.getByRole('button', { name: 'Nova conta' }).first().click()
  const form = page.locator('form').filter({ hasText: 'Nova conta' })
  await form.getByRole('textbox', { name: 'Nome' }).fill('Conta Fluxo')
  await form.getByRole('textbox', { name: 'Saldo atual' }).fill('1000,00')
  await form.getByRole('button', { name: 'Criar conta' }).click()
  await expect(page.getByText('Conta salva.').first()).toBeVisible()
  await expect(page.getByText('R$ 1.000,00').first()).toBeVisible()

  await quickAction(page, 'D')
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('textbox', { name: 'Valor' }).fill('64,30')
  await dialog.getByRole('textbox', { name: 'Descrição' }).fill('Feira do fluxo')
  await dialog.getByRole('radio', { name: 'Alimentação' }).click()
  await dialog.getByRole('button', { name: 'Salvar despesa' }).click()
  await expect(page.getByText('Transação salva.').first()).toBeVisible()
  await expect(page.getByText('R$ 935,70').first()).toBeVisible()

  await page.goto('/financas/transacoes')
  await page.getByPlaceholder('Buscar por descrição ou valor').fill('64,30')
  await expect(page.getByText('Feira do fluxo')).toBeVisible()
  await expect(page.getByText('1 transação')).toBeVisible()
})

test('garage: vehicle and fueling', async ({ page }) => {
  await signIn(page)
  await page.goto('/veiculos')
  await page.getByRole('button', { name: 'Novo veículo' }).first().click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('textbox', { name: 'Nome ou apelido' }).fill('Moto do fluxo')
  await dialog.getByRole('textbox', { name: 'Marca' }).fill('Honda')
  await dialog.getByRole('textbox', { name: 'Modelo' }).fill('CG 160')
  await dialog.getByRole('textbox', { name: 'Ano' }).fill('2023')
  await dialog.getByRole('textbox', { name: 'Km atual' }).fill('1000')
  await dialog.getByRole('button', { name: 'Cadastrar veículo' }).click()
  await expect(page.getByText('Veículo salvo').first()).toBeVisible()
  await expect(page.getByText('Moto do fluxo').first()).toBeVisible()

  await quickAction(page, 'A')
  const fueling = page.getByRole('dialog')
  // After the registration reading (G3: a later reading cannot have fewer km).
  await fueling.getByRole('textbox', { name: 'Hora' }).fill('15:00')
  await fueling.getByRole('textbox', { name: 'Km atual' }).fill('1150')
  await fueling.getByRole('textbox', { name: 'Litros' }).fill('7,30')
  await fueling.getByRole('textbox', { name: 'Valor total' }).fill('46,36')
  await fueling.getByRole('button', { name: 'Salvar abastecimento' }).click()
  await expect(page.getByText('Abastecimento registrado').first()).toBeVisible()
  await page.goto('/veiculos')
  await expect(page.getByText('1.150', { exact: false }).first()).toBeVisible()
})

test('reading: book, progress and note', async ({ page }) => {
  await signIn(page)
  await page.goto('/livros')
  await page.getByRole('button', { name: 'Adicionar livro' }).first().click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('textbox', { name: 'Título' }).fill('Livro do fluxo')
  await dialog.getByRole('textbox', { name: 'Autor' }).fill('Autora Teste')
  await dialog.getByRole('textbox', { name: 'Número de páginas' }).fill('200')
  await dialog.getByRole('button', { name: 'Adicionar à estante' }).click()
  await expect(page.getByText('Livro salvo.').first()).toBeVisible()

  await page.getByRole('button', { name: 'Começar a ler' }).click()
  await expect(page.getByText('Lendo agora')).toBeVisible()
  await page.getByRole('textbox', { name: 'Página atual' }).fill('50')
  await page.getByRole('button', { name: 'Salvar progresso' }).click()
  await expect(page.getByText('Página 50 de 200')).toBeVisible()
  await expect(page.getByText('25%')).toBeVisible()

  await page.getByRole('link', { name: 'Ver detalhes e anotações' }).click()
  await page.getByRole('button', { name: 'Nova anotação' }).click()
  const note = page.getByRole('dialog')
  await note.getByRole('textbox', { name: 'Anotação' }).fill('Primeira anotação do fluxo.')
  await page.keyboard.press('Control+Enter')
  await expect(page.getByText('Anotação salva.').first()).toBeVisible()
  await expect(page.getByText('Primeira anotação do fluxo.')).toBeVisible()
  await expect(page.getByText('p. 50')).toBeVisible()
})

test('export the data and open the API docs', async ({ page }) => {
  await signIn(page)
  await page.goto('/configuracoes#dados')
  const download = page.waitForEvent('download')
  await page.getByRole('link', { name: 'Exportar dados' }).click()
  expect((await download).suggestedFilename()).toMatch(/^prumo-teste-\d{8}-\d{4}\.zip$/)

  await page.goto('/api/docs')
  await expect(page.getByRole('heading', { name: /Prumo API/ })).toBeVisible()
})
