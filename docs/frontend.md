# Frontend e design

## Stack

| Uso | Escolha |
|---|---|
| Base | Vue 3 (`<script setup lang="ts">`), TypeScript strict, Vite, pnpm |
| Rotas | Vue Router |
| Dados do servidor | TanStack Query (`@tanstack/vue-query`) |
| Estado de interface | Pinia (sessão e usuário atual, tema) |
| Cliente da API | `openapi-fetch` com tipos gerados por `openapi-typescript` |
| Primitivos acessíveis | Reka UI (headless: diálogos, popovers, selects, tabs, menus) |
| Formulários | Zod para validação, com erros da API mapeados para os campos (`lib/forms.ts`) |
| i18n | vue-i18n, `pt-BR` padrão |
| Gráficos | componentes próprios em CSS/SVG atrás de `<PChart>` (sem biblioteca; ver D17) |
| Ícones | Lucide (`@lucide/vue`) atrás de `<PIcon>`, com nomes semânticos em `src/ui/icons.ts` (D16) |
| Fonte | Figtree variável, hospedada pela aplicação (`@fontsource-variable/figtree`, D18) |
| Testes | Vitest + Vue Test Utils; Playwright para screenshots e E2E |
| Qualidade | ESLint, Prettier, Stylelint, `vue-tsc` |

## Estrutura

```
frontend/src/
├── app/            # main.ts, App.vue, router, query client, i18n, registro de módulos, stores (sessão, tema)
├── design/         # tokens.css (primitivos), scales.css, themes/light.css, themes/dark.css, tones.css, base.css
├── ui/             # componentes base P*: toda a aparência mora aqui
├── layouts/        # AppShell (trilho, barra inferior, Registrar, menu da conta), AuthLayout
├── lib/            # api/ (cliente e schema gerado), format.ts, forms.ts, errors.ts, media.ts
├── system/         # telas de plataforma: login, início, configurações, erros, /dev/ui
└── modules/
    ├── index.ts    # lista de módulos instalados (ordem padrão: finance, garage, reading)
    ├── finance/
    ├── garage/
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
  id: 'garage',                         // igual ao id do backend; também é o tom de cor (data-tone)
  icon: 'car',                          // nome semântico de src/ui/icons.ts
  nav: { labelKey: 'garage.nav', route: 'garage.home' },
  descriptionKey: 'garage.description', // texto da lista de módulos em Configurações
  routes,
  dashboardWidget: () => import('./widgets/GarageWidget.vue'), // recebe a prop `summary`
  quickActions: [
    { id: 'garage.update-km', labelKey: 'garage.actions.updateKm', icon: 'gauge', shortcut: 'K',
      pinned: true, component: () => import('./forms/UpdateKmDialog.vue') },
    { id: 'garage.add-fueling', labelKey: 'garage.actions.addFueling', icon: 'fuel', shortcut: 'A',
      pinned: true, component: () => import('./forms/FuelingDialog.vue') },
  ],
  messages: { 'pt-BR': () => import('./locales/pt-BR.json') },
})
```

O registro (`app/registry.ts`) monta rotas, itens de navegação, widgets do Início e o menu Registrar, respeitando os módulos ativos e a ordem de `GET /api/v1/modules`. Módulos não importam outros módulos. Os textos de um módulo ficam sob o id dele (`garage.nav`).

As ações rápidas cumprem a regra de que registros frequentes ficam a no máximo dois cliques de qualquer tela:

- **Menu Registrar**: botão do trilho (ou FAB no celular) e tecla **N** em qualquer tela. Dentro do menu, a tecla de `shortcut` executa a ação.
- **Chips do Início**: ações com `pinned: true`.
- O componente da ação é um diálogo que recebe `v-model:open`.

## Camadas de estilo

O design vai mudar. Toda a arquitetura de estilo existe para que um redesign seja barato.

1. **Primitivos** (`design/tokens.css`): paleta crua e famílias de fonte (`--p-sand-100`, `--p-orange-500`…). Componentes nunca usam primitivos diretamente.
2. **Escalas** (`design/scales.css`): tipografia, espaço, raios, movimento e medidas, iguais nos dois temas.
3. **Semânticos** (`design/themes/light.css` e `dark.css`): cores e sombras que os componentes usam. Valores que dependem de cor ficam no tema (inclusive sombras como `--shadow-focus`).
4. **Tons** (`design/tones.css`): componentes recebem `tone` (id de módulo ou status), renderizado como `data-tone`. Cada tom expõe as mesmas cinco variáveis (`--tone`, `--tone-container`, `--tone-on-container`, `--tone-soft`, `--tone-softer`), então nenhum componente ramifica por tom.
5. **Componentes** (`src/ui/`): consomem apenas tokens semânticos e tons.
6. **Layouts** (`src/layouts/`): estrutura da aplicação.
7. **Telas**: compõem componentes; o CSS delas trata só de layout com tokens de espaço. Texto estilizado usa `<PText>`.

Tema: `data-theme="light|dark"` no `<html>`. A preferência (`system`, `light`, `dark`) vem do servidor; `system` segue `prefers-color-scheme`. A última preferência fica em `localStorage` para o `index.html` aplicar o tema antes da primeira pintura. Os tokens são definidos em `[data-theme]`, então dois temas podem coexistir na mesma página (vitrine).

O Stylelint proíbe cor (hex, nomeada, `rgb()`…), fonte, peso, tamanho de fonte, sombra e raio literais fora de `src/design/`. O ESLint proíbe texto fixo em templates (`vue/no-bare-strings-in-template`) e importar Lucide ou Reka UI fora de `src/ui/`.

Componentes base (`src/ui/`, exportados por `@/ui`):

| Grupo | Componentes |
|---|---|
| Ações | `PButton` (primary, outline, tonal, ghost, danger, chip; md/lg), `PIconButton`, `PFab` (trilho ou flutuante), `PLink` |
| Formulário | `PField`, `PInput` (afixos, ícone, revelar senha, calculado), `PNumberInput`, `PMoneyInput` (centavos), `PTextarea`, `PSelect`, `PCombobox` (com criação), `PDateInput` (data ou hora, nativo), `PCheckbox`, `PSwitch`, `PSegmented`, `PStepper`, `PSwatchPicker`, `PSearchField`, `PChoiceCards`, `PThemePreview` |
| Exibição | `PText`, `PCard`, `PPanel`, `PStatCard`, `PTile` (quadrado ou círculo), `PBadge`, `PStatus`, `PKbd`, `PAvatar`, `PProgress`, `PRing`, `PDateBadge`, `PDescriptionList`, `PDivider`, `PLogo` |
| Navegação e listas | `PPageHeader`, `PTabs` + `PTabPanel`, `PNavList`, `PList` + `PListItem`, `PTable` (vira lista em contêiner estreito), `PSortableList` (arrastar ou setas) |
| Sobreposições | `PDialog` (tela cheia no celular), `PConfirmDialog`, `PPopover`, `PMenu`, `PCommand`, `PDrawer`, `PToaster` + `useToast()` |
| Estados | `PEmptyState` (simples ou card), `PSkeleton`, `PSpinner`, `PAlert`, `PNote`, `PQueryState` (carregando, erro com "Tentar de novo", vazio) |
| Base | `PIcon`, `PChart` (barras com destaque e média, barras agrupadas, rosca, barra empilhada) |

A vitrine `/dev/ui` (só em desenvolvimento) mostra todos os componentes, com variantes e estados, nos dois temas lado a lado. Sobreposições aparecem em modo inline (sem portal) para herdar o tema da coluna. Ela tem também **composições**: telas do design remontadas só com `src/ui/` e dados fictícios (`?view=home`, `?view=states`, com `&theme=dark`), usadas para comparar com o design e validar redesigns.

## Design system atual (v1)

**Direção:** variante C do Claude Design, ajustada. Neutros quentes, acento grafite (o botão principal é grafite, não colorido) e cor só como identidade de módulo. Cards grandes por módulo no Início, gráficos e barras de progresso; sóbria e um pouco densa.

**Referência:** `design/v1/` (`prumo.html` e uma imagem por prancha, em 2×).

### Cores

| Token semântico | Claro | Escuro | Uso |
|---|---|---|---|
| `--color-bg` | `#F4F3F1` | `#131215` | fundo da página |
| `--color-surface` (`-raised`) | `#FFFFFF` | `#1D1C20` | cards, diálogos, menus |
| `--color-surface-inset` | `#F7F6F4` | `#26252A` | painel interno, hover de tabela |
| `--color-surface-tint` | `#F4F3F1` | `#26252A` | abas, item destacado, nota, bloco de data |
| `--color-fill` | `#F0EEEB` | `#2E2C32` | chips, trilho das barras, segmentado |
| `--color-divider` | `#EFEDEA` | `#2A282E` | divisórias de lista e tabela |
| `--color-border` | `#E6E3DF` | `#34323A` | bordas de campo e botão |
| `--color-border-strong` | `#D3CFCA` | `#4A4750` | borda tracejada, switch desligado |
| `--color-text` | `#1C1B1F` | `#EEEDF0` | texto |
| `--color-text-secondary` | `#47454C` | `#CAC7CF` | texto secundário |
| `--color-text-muted` | `#67646C` | `#A3A0A9` | legendas (≥ 4,5:1) |
| `--color-neutral` | `#8E8A93` | `#8E8A93` | critério secundário em gráficos |
| `--color-accent` / `-contrast` | `#1C1B1F` / `#FFFFFF` | `#EEEDF0` / `#131215` | botão principal, item ativo, foco |
| `--color-danger` / `-container` / `--color-on-danger-container` | `#C2362B` / `#FBE4E1` / `#8F2219` | `#FF7A6B` / `#3D1814` / `#FFB4AA` | exclusão, erro |
| `--color-scrim` | grafite 42% | preto 60% | fundo de diálogo |

`--color-success` e `--color-warning` (com `-container` e `--color-on-*-container`) não existem no design v1: derivam do verde de Finanças e do laranja de Veículos.

### Cores por módulo

Cada módulo tem cinco tokens: principal, container, texto sobre o container, `-soft` (histórico em gráficos) e `-softer` (fim da rampa de categorias).

| Módulo | Claro | Escuro |
|---|---|---|
| Finanças (`finance`) | `#24A06B` · `#E1F3EA` · `#17643F` · `#7CCBA3` · `#BFE6D1` | `#4CC98F` · `#15301F` · `#8FE0B8` · `#2E8A62` · `#1F5C42` |
| Veículos (`garage`) | `#E4672E` · `#FBE9DF` · `#8A3A12` · `#F3C2A6` · `#FBE9DF` | `#F08A55` · `#3A2418` · `#F6B892` · `#7A4127` · `#3A2418` |
| Livros (`reading`) | `#6F57E8` · `#ECE8FD` · `#4A34B5` · `#C9BEF8` · `#ECE8FD` | `#9C8BFF` · `#262047` · `#C3B8FF` · `#4B3F8F` · `#262047` |

Um módulo novo escolhe um matiz livre, gera os cinco tokens com a mesma luminosidade dos atuais nos dois temas e adiciona um bloco `[data-tone='<id>']` em `tones.css`. No Android, o trio vira primary / primaryContainer / onPrimaryContainer do esquema do módulo. Cores de usuário (contas, categorias) usam `--color-swatch-*`.

### Tipografia

Figtree variável (400 a 800), corpo de 15 px com `line-height` 1,45 e algarismos tabulares em toda a interface. Números no formato pt-BR (`R$ 1.234,56`, `17/11/2026`, `14:30`, `12.345 km`).

| Estilo (`PText`) | Tamanho / peso | Token |
|---|---|---|
| `h1` | 32 / 700, −0,02em | `--text-4xl` |
| `title` | 26 / 700 | `--text-3xl` |
| `number-xl` | 32 / 800 (símbolo em 53%) | `--text-4xl` |
| `number-l` | 22 / 800 | `--text-2xl` |
| `h2` | 17 / 700 | `--text-xl` |
| `strong` | 16 / 700 | `--text-lg` |
| `body`, `h3` | 15 / 400 e 700 | `--text-base` |
| `overline` | 14 / 600, cor muted | `--text-md` |
| `sm`, `xs` | 13 e 12 | `--text-sm`, `--text-xs` |

Também existem `--text-2xs` (11), `--text-2xl-plus` (24, título no celular) e `--text-5xl` (44, chamada do login).

### Espaço, forma e movimento

- **Espaço:** `--space-N` = N × 4 px (meios passos `-0-5`, `-1-5`, `-2-5`, `-3-5`, `-4-5`, `-6-5`). Gap entre cards 16, padding de card 20, de diálogo 24, margem da página 32.
- **Raios:** `--radius-sm` 8, `-md` 12 (campo), `-lg` 18 (painel), `-xl` 24 (card), `-2xl` 28 (diálogo), `-full` (botão e chip). De componente: `--radius-menu` 20, `-menu-item` 14, `-fab` 16, `-indicator` 16, `-avatar` 14, `-tile` 12/18/26, `-alert` 16, `-note` 14.
- **Sombras:** `--shadow-sm` (cards; nenhuma no escuro) e `--shadow-lg` (diálogos, menus, popovers, FAB flutuante). Não há sombra média.
- **Medidas:** controles de 44 px (36 e 52 nas variantes), abas de 40, trilho de 88, página de até 1260.
- **Movimento:** o prumo do logo balança e para (2,4 s, uma vez); anéis e barras se desenham ao entrar (1 s, `--easing-standard`); tudo desliga com `prefers-reduced-motion`.

### Ícones e gráficos

- **Ícones:** Lucide, traço 2 (1,8 no tamanho xl), 16/20/28/36 px. Os nomes semânticos (`car`, `wallet`, `book`, `fuel`, `gauge`…) ficam em `src/ui/icons.ts`. O logotipo (prumo) é um SVG próprio em `PLogo`.
- **Gráficos:** a cor do módulo marca o dado principal (última barra, série principal), o tom `-soft` marca o histórico, o neutro marca a segunda série, e categorias usam a rampa do tom (texto, principal, soft, softer). Média em linha tracejada com rótulo. Todo gráfico tem descrição acessível e lista de valores para leitores de tela.

### Navegação

- **Desktop:** trilho com logo, botão Registrar, Início, módulos ativos, Módulos (leva a Configurações › Módulos), Configurações e o avatar (menu da conta: tema, Configurações, Sair). Item ativo de módulo usa o container da cor dele; Início usa grafite.
- **Celular (< 840 px):** barra inferior com Início, até três módulos e Mais (gaveta com o restante, Configurações e Sair), FAB flutuante para Registrar, avatar no topo do Início. Diálogos viram tela cheia com rodapé fixo; tabelas viram listas.

### Comparação com o design

`make screenshots` captura login, Início, Configurações, Início no celular, a vitrine e as composições (API simulada, relógio em 17/11/2026 14:30, densidade 2×) em `frontend/e2e/output/` e monta imagens lado a lado (design | implementação) em `frontend/e2e/output/compare/`.

### Divergências conhecidas entre o design v1 e os docs

Decididas na Fase 0 (D22): login só por usuário (sem e-mail), sem foto de perfil, usuário não editável, tema guardado na conta, sem busca global por enquanto.

Ainda abertas, a decidir na fase de cada módulo:

- **Veículos:** combustível padrão do veículo; "óleo utilizado" na troca; datas estimadas pelo ritmo de uso (km/dia); km rodados no mês; listas entre veículos (abastecimentos, manutenções, trocas, oficinas); estatísticas da oficina no autocompletar; peça sem quantidade no formulário e mão de obra como linha "Serviço"; histórico de consumo por ciclo.
- **Finanças:** hora na transação (`occurred_on` é data); período da fatura (o design inclui a compra do dia do fechamento, F4 não); excluir categoria em uso (F8 proíbe); categorias sugeridas como escolha no primeiro uso (F7 cria automaticamente); "saldo atual" no cadastro e "Ajustar saldo"; histórico de 6 meses na visão geral; busca por valor.
- **Livros:** previsão de término e ritmo de leitura; lista de todas as anotações; data editável na anotação; `owned` ("tenho") sem lugar na interface.
- **Início:** seções "Vem aí" e "Atividade recente" (agregações entre módulos que o dashboard ainda não tem).

## Como fazer um redesign

1. Exporte o novo design para `design/v2/` e atualize `design/README.md` com a versão ativa.
2. Peça ao Claude Code um comparativo v1 × v2: o que muda em tokens, em componentes, em layouts e em estrutura de telas.
3. Ajuste os tokens (`src/design/`). Mudanças só de cor, fonte, raio ou espaçamento terminam aqui.
4. Ajuste os componentes (`src/ui/`) e valide na vitrine nos dois temas.
5. Ajuste os layouts (`src/layouts/`).
6. Só então mude telas cuja **estrutura** mudou (não apenas a aparência).
7. Atualize as composições de `/dev/ui`, compare screenshots (`make screenshots`) com as imagens do novo design e atualize a seção "Design system atual" deste documento.

## Dados, formulários e formatação

- Chaves de query começam pelo id do módulo: `['garage', 'vehicles', id]`. Toda mutation invalida as chaves afetadas, incluindo `['dashboard']`. As da plataforma ficam em `system/api.ts` (`['preferences']`, `['modules']`, `['dashboard']`, `['sessions']`).
- Pinia guarda só estado de interface e sessão; dados do servidor ficam no TanStack Query.
- `unwrap()` transforma o resultado do `openapi-fetch` em dados ou em `ApiError` (`status`, `code`, `fields`, `details`). Um 401 durante o uso leva ao login.
- Erros da API com `fields` são mapeados para os campos (`apiFieldErrors`); o `code` é traduzido via i18n (`errors.<code>`, `fieldErrors.<code>`).
- `lib/format.ts` concentra a formatação com `Intl`, usando idioma, fuso e moeda das preferências: dinheiro a partir de centavos, km, litros a partir de mililitros, datas (data pura nunca muda de dia), data-hora e "Hoje"/"Ontem".
- Nenhum cálculo de regra de negócio no frontend. Cálculos de conveniência em formulários (como o total parcial de uma manutenção enquanto se digita) são permitidos, mas o valor exibido depois de salvo é sempre o da API.

## Responsividade e acessibilidade

- Desktop primeiro, responsivo até tablet e celular (ver Navegação).
- Contraste AA nos dois temas, foco visível, navegação completa por teclado (garantida em boa parte pelos primitivos do Reka UI), link "Pular para o conteúdo", lista reordenável por teclado e anúncios para leitores de tela.
