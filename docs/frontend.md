# Frontend e design

## Stack

| Uso | Escolha |
|---|---|
| Base | Vue 3 (`<script setup lang="ts">`), TypeScript strict, Vite, pnpm |
| Rotas | Vue Router |
| Dados do servidor | TanStack Query (`@tanstack/vue-query`) |
| Estado de interface | Pinia (usuário atual, preferências, tema) |
| Cliente da API | `openapi-fetch` com tipos gerados por `openapi-typescript` |
| Primitivos acessíveis | Reka UI (headless: diálogos, popovers, selects, tabs, menus) |
| Formulários | Zod para validação, com erros da API mapeados para os campos |
| i18n | vue-i18n, `pt-BR` padrão |
| Gráficos | biblioteca escolhida na Fase 0 conforme o design, sempre atrás de `<PChart>` |
| Ícones | conjunto escolhido na Fase 0 conforme o design, sempre atrás de `<PIcon>` |
| Testes | Vitest + Vue Test Utils; Playwright para screenshots e E2E |
| Qualidade | ESLint, Prettier, Stylelint, `vue-tsc` |

## Estrutura

```
frontend/src/
├── app/            # main.ts, App.vue, router, query client, i18n, registro de módulos
├── design/         # tokens.css (primitivos), themes/light.css, themes/dark.css, base.css
├── ui/             # componentes base P*: toda a aparência mora aqui
├── layouts/        # AppShell (navegação, topo, ações rápidas), AuthLayout
├── lib/            # api/ (cliente e schema gerado), format.ts, utilitários
├── system/         # telas de plataforma: login, início, configurações, /dev/ui
└── modules/
    ├── index.ts    # lista de módulos instalados
    ├── garage/
    ├── finance/
    └── reading/
```

Cada módulo:

```
modules/garage/
├── index.ts        # definição do módulo
├── routes.ts
├── api.ts          # queries e mutations (TanStack Query) do módulo
├── pages/
├── components/     # componentes específicos do módulo, compostos com src/ui
├── forms/          # formulários e diálogos de registro
├── widgets/        # widget do Início
└── locales/pt-BR.json
```

## Sistema de módulos

```ts
// modules/garage/index.ts
export default defineModule({
  id: 'garage',                         // igual ao id do backend
  icon: 'car',
  nav: { labelKey: 'garage.nav', route: 'garage.home' },
  routes,
  dashboardWidget: () => import('./widgets/GarageWidget.vue'),
  quickActions: [
    { id: 'garage.update-km', labelKey: 'garage.actions.updateKm', icon: 'gauge',
      component: () => import('./forms/UpdateKmDialog.vue') },
    { id: 'garage.add-fueling', labelKey: 'garage.actions.addFueling', icon: 'fuel',
      component: () => import('./forms/FuelingDialog.vue') },
  ],
  messages: { 'pt-BR': () => import('./locales/pt-BR.json') },
})
```

O registro em `app/` monta rotas, itens de navegação, widgets do Início e o menu global de ações rápidas, respeitando os módulos ativos e a ordem vindos de `GET /api/v1/modules`. Módulos não importam outros módulos.

As ações rápidas existem para cumprir a regra de que registros frequentes (atualizar km, abastecer, lançar despesa, atualizar página) ficam a no máximo dois cliques de qualquer tela.

## Camadas de estilo

O design vai mudar. Toda a arquitetura de estilo existe para que um redesign seja barato.

1. **Primitivos** (`design/tokens.css`): paleta crua e escalas (`--p-gray-50`, `--p-teal-600`…). Componentes nunca usam primitivos diretamente.
2. **Semânticos** (`design/themes/light.css` e `dark.css`): o que os componentes usam.
   - Cor: `--color-bg`, `--color-surface`, `--color-surface-raised`, `--color-border`, `--color-text`, `--color-text-muted`, `--color-accent`, `--color-accent-contrast`, `--color-success`, `--color-warning`, `--color-danger`, `--color-module-garage`, `--color-module-finance`, `--color-module-reading`
   - Tipografia: `--font-sans`, `--font-numeric`, `--text-xs` … `--text-2xl`, `--weight-*`, `--leading-*`
   - Espaço, forma e movimento: `--space-1` … `--space-12`, `--radius-sm|md|lg|full`, `--shadow-sm|md|lg`, `--duration-fast|base`, `--easing-standard`
3. **Componentes** (`src/ui/`): consomem apenas tokens semânticos.
4. **Layouts** (`src/layouts/`): estrutura da aplicação.
5. **Telas**: compõem componentes; o CSS delas trata só de layout com tokens de espaço.

Tema: `data-theme="light|dark"` no `<html>`; a preferência `system` segue `prefers-color-scheme`. O Stylelint proíbe cores literais fora de `src/design/`.

Componentes base previstos (ajustar ao design na Fase 0): `PButton`, `PIconButton`, `PField`, `PInput`, `PNumberInput`, `PMoneyInput`, `PTextarea`, `PSelect`, `PCombobox`, `PDateInput`, `PDateTimeInput`, `PCheckbox`, `PSwitch`, `PSegmented`, `PCard`, `PStatCard`, `PProgress`, `PBadge`, `PStatus`, `PTabs`, `PTable`, `PList`, `PDialog`, `PDrawer`, `PPopover`, `PMenu`, `PToast`, `PEmptyState`, `PSkeleton`, `PPageHeader`, `PIcon`, `PChart`, `PAvatar`.

A vitrine `/dev/ui` (só em desenvolvimento) mostra todos os componentes, com suas variantes e estados, nos dois temas lado a lado.

## Design system atual (v1)

**Direção:** variante C do Claude Design, ajustada. Expressiva, com uma cor de identidade por módulo, cards grandes por módulo no Início, gráficos e barras de progresso; porém sóbria, menos colorida, um pouco mais densa e com tipografia sóbria.

**Referência:** `design/v1/`.

**Tokens:** _a preencher na Fase 0 com os valores extraídos de `design/v1/`_ (paleta primitiva, mapeamento semântico nos dois temas, famílias tipográficas e escala, espaçamento, raios, sombras, cores por módulo, conjunto de ícones e estilo dos gráficos).

## Como fazer um redesign

1. Exporte o novo design para `design/v2/` e atualize `design/README.md` com a versão ativa.
2. Peça ao Claude Code um comparativo v1 × v2: o que muda em tokens, em componentes, em layouts e em estrutura de telas.
3. Ajuste os tokens (`src/design/`). Mudanças só de cor, fonte, raio ou espaçamento terminam aqui.
4. Ajuste os componentes (`src/ui/`) e valide na vitrine nos dois temas.
5. Ajuste os layouts (`src/layouts/`).
6. Só então mude telas cuja **estrutura** mudou (não apenas a aparência).
7. Compare screenshots (Playwright) com as imagens do novo design e atualize a seção "Design system atual" deste documento.

## Dados, formulários e formatação

- Chaves de query começam pelo id do módulo: `['garage', 'vehicles', id]`. Toda mutation invalida as chaves afetadas, incluindo `['dashboard']`.
- Pinia guarda só estado de interface e sessão; dados do servidor ficam no TanStack Query.
- Erros da API com `fields` são mapeados para os campos do formulário; o `code` é traduzido via i18n.
- `lib/format.ts` concentra a formatação com `Intl`, usando idioma, fuso e moeda das preferências: dinheiro a partir de centavos, km, litros a partir de mililitros, datas e data-hora.
- Nenhum cálculo de regra de negócio no frontend. Cálculos de conveniência em formulários (como o total parcial de uma manutenção enquanto se digita) são permitidos, mas o valor exibido depois de salvo é sempre o da API.

## Responsividade e acessibilidade

- Desktop primeiro, responsivo até tablet e celular. No celular, a navegação vira gaveta e tabelas viram listas.
- Contraste AA nos dois temas, foco visível, navegação completa por teclado (garantida em boa parte pelos primitivos do Reka UI).
