<script setup lang="ts">
/**
 * Every base component with its variants and states. Rendered twice by DevUiPage, once per
 * theme. Overlays render inline (no portal) so they inherit the theme of their column.
 */
import { ref } from 'vue'

import { iconNames, useToast } from '@/ui'
import {
  PAlert,
  PAvatar,
  PBadge,
  PBookCover,
  PButton,
  PCard,
  PCardFace,
  PChart,
  PCheckbox,
  PChipChoice,
  PChoiceCards,
  PCombobox,
  PCommand,
  PConfirmDialog,
  PDateBadge,
  PDateInput,
  PDescriptionList,
  PDialog,
  PDivider,
  PDrawer,
  PEmptyState,
  PFab,
  PField,
  PFileButton,
  PIcon,
  PIconButton,
  PIconPicker,
  PInput,
  PKbd,
  PLink,
  PList,
  PListItem,
  PLogo,
  PMenu,
  PMoneyInput,
  PMonthNav,
  PNavList,
  PNote,
  PNumberInput,
  PPageHeader,
  PPopover,
  PProgress,
  PQueryState,
  PRing,
  PSearchField,
  PSegmented,
  PSelect,
  PSkeleton,
  PSortableList,
  PSpinner,
  PStatCard,
  PStatus,
  PStepper,
  PSwatchPicker,
  PSwitch,
  PTable,
  PTabPanel,
  PTabs,
  PText,
  PTextarea,
  PThemePreview,
  PTile,
} from '@/ui'
import { ApiError } from '@/lib/api/errors'
import { moneyAmount } from '@/lib/format'

import ShowcaseRow from './ShowcaseRow.vue'
import ShowcaseSection from './ShowcaseSection.vue'

defineProps<{ theme: 'light' | 'dark' }>()

const toast = useToast()
const text = ref('Moto Peças Rocha')
const password = ref('prumo-demo-01')
const km = ref<number | null>(18300)
const liters = ref<number | null>(5)
const cents = ref<number | null>(5842)
const notes = ref('')
const account = ref('nubank')
const workshop = ref<string | null>(null)
const kind = ref('expense')
const on = ref(true)
const off = ref(false)
const checked = ref(true)
const color = ref('blue')
const page = ref(212)
const bigCents = ref<number | null>(6430)
const month = ref('2026-11')
const chip = ref('food')
const chips = [
  { value: 'food', label: 'Alimentação', icon: 'utensils' as const },
  { value: 'fuel', label: 'Combustível', icon: 'fuel' as const },
  { value: 'home', label: 'Moradia', icon: 'home' as const },
  { value: 'fun', label: 'Lazer', icon: 'ticket' as const },
]
const pickedIcon = ref('vault')
const iconChoices = [
  { value: 'bank', icon: 'bank' as const, label: 'Banco' },
  { value: 'vault', icon: 'vault' as const, label: 'Cofre' },
  { value: 'wallet', icon: 'wallet' as const, label: 'Carteira' },
  { value: 'trending-up', icon: 'trending-up' as const, label: 'Investimento' },
  { value: 'card', icon: 'card' as const, label: 'Cartão' },
]
const userColors = [
  'green',
  'teal',
  'cyan',
  'blue',
  'indigo',
  'violet',
  'pink',
  'red',
  'orange',
  'amber',
  'gray',
] as const
const themeChoice = ref<'light' | 'dark' | 'system'>('light')
const tab = ref('maintenances')
const sortable = ref([
  { id: 'finance', label: 'Finanças' },
  { id: 'garage', label: 'Veículos' },
  { id: 'reading', label: 'Livros' },
])
const date = ref('2026-11-17')
const time = ref('14:30')
const dialogOpen = ref(false)
const drawerOpen = ref(false)
const popoverOpen = ref(false)

const accounts = [
  { value: 'nubank', label: 'Nubank' },
  { value: 'inter', label: 'Inter' },
  { value: 'wallet', label: 'Carteira' },
]
const workshops = [
  {
    value: 'rocha',
    label: 'Moto Peças Rocha',
    description: '3 manutenções · última em 03/09/2026',
  },
  { value: 'centro', label: 'Auto Center Centro' },
]
const kinds = [
  { value: 'expense', label: 'Despesa' },
  { value: 'income', label: 'Receita' },
  { value: 'transfer', label: 'Transf.' },
]
const swatches = [
  { value: 'blue', label: 'Azul', color: 'var(--color-swatch-blue)' },
  { value: 'violet', label: 'Violeta', color: 'var(--color-swatch-violet)' },
  { value: 'orange', label: 'Laranja', color: 'var(--color-swatch-orange)' },
  { value: 'green', label: 'Verde', color: 'var(--color-swatch-green)' },
  { value: 'pink', label: 'Rosa', color: 'var(--color-swatch-pink)' },
  { value: 'cyan', label: 'Ciano', color: 'var(--color-swatch-cyan)' },
  { value: 'gray', label: 'Cinza', color: 'var(--color-swatch-gray)' },
]
const themes = [
  { value: 'light' as const, label: 'Claro' },
  { value: 'dark' as const, label: 'Escuro' },
  { value: 'system' as const, label: 'Automático', description: 'segue o sistema' },
]
const tones = ['finance', 'garage', 'reading', 'danger', 'success', 'warning', 'neutral'] as const
const colorTokens = [
  ['--color-bg', 'fundo'],
  ['--color-surface', 'cards'],
  ['--color-surface-inset', 'painel interno'],
  ['--color-fill', 'trilhos, chips'],
  ['--color-border', 'bordas'],
  ['--color-text', 'texto, botão principal'],
  ['--color-text-secondary', 'texto secundário'],
  ['--color-text-muted', 'legendas'],
  ['--color-danger', 'exclusão, erro'],
] as const
const columns = [
  { key: 'date', label: 'Data' },
  { key: 'description', label: 'Descrição' },
  { key: 'amount', label: 'Valor', align: 'end' as const },
]
const rows = [
  { id: '1', date: '16/11', description: 'Supermercado', amount: -21240 },
  { id: '2', date: '12/11', description: 'Site institucional', amount: 150000 },
]
const commandGroups = [
  {
    label: 'Veículos',
    items: [
      { id: 'km', label: 'Atualizar km', icon: 'gauge' as const, tone: 'garage', shortcut: 'K' },
      { id: 'fuel', label: 'Abastecimento', icon: 'fuel' as const, tone: 'garage', shortcut: 'A' },
    ],
  },
  {
    label: 'Finanças',
    items: [
      { id: 'expense', label: 'Despesa', icon: 'minus' as const, tone: 'finance', shortcut: 'D' },
    ],
  },
]
const menuItems = [
  { type: 'label' as const, label: 'Tema' },
  { label: 'Claro', icon: 'sun' as const, checked: true },
  { label: 'Escuro', icon: 'moon' as const },
  { type: 'separator' as const },
  { label: 'Sair', icon: 'logout' as const, danger: true },
]
const networkError = ApiError.network(new Error('offline'))
</script>

<template>
  <div class="showcase">
    <ShowcaseSection title="Cores" note="Tokens semânticos deste tema; tons por módulo e status.">
      <div class="showcase__tokens">
        <div v-for="[token, use] in colorTokens" :key="token" class="showcase__token">
          <span class="showcase__swatch" :style="{ background: `var(${token})` }" />
          <span>
            <code>{{ token }}</code>
            <PText variant="xs" tone="muted">{{ use }}</PText>
          </span>
        </div>
      </div>
      <ShowcaseRow label="tones">
        <span v-for="tone in tones" :key="tone" class="showcase__tone" :data-tone="tone">
          <i /><i /><i /><i /><i />
          <code>{{ tone }}</code>
        </span>
      </ShowcaseRow>
      <ShowcaseRow label="user colors (swatch-*)">
        <PTile v-for="name in userColors" :key="name" icon="wallet" :tone="`swatch-${name}`" />
      </ShowcaseRow>
    </ShowcaseSection>

    <ShowcaseSection title="Tipografia · Figtree">
      <PText variant="h1">Boa tarde, Henrique</PText>
      <PText variant="title">Entrar</PText>
      <PText variant="heading">Honda CG 160 Fan</PText>
      <PText variant="number-xl"><small>R$</small> 7.154,27</PText>
      <PText variant="number-l">18.420 km</PText>
      <PText variant="h2">Próxima troca de óleo</PText>
      <PText variant="lead" tone="secondary">Texto de abertura, maior.</PText>
      <PText>Texto corrido para descrições e campos.</PText>
      <PText variant="overline">Terça, 17 de novembro</PText>
      <PText variant="sm" tone="muted">Último registro: 18.420 km</PText>
    </ShowcaseSection>

    <ShowcaseSection title="Ícones (Lucide)" note="Sempre por <PIcon>. Tamanhos sm, md, lg, xl.">
      <div class="showcase__icons">
        <span v-for="name in iconNames" :key="name" class="showcase__icon" :title="name">
          <PIcon :name="name" />
          <PText variant="xs" tone="muted" as="span">{{ name }}</PText>
        </span>
      </div>
      <ShowcaseRow label="size">
        <PIcon name="car" size="sm" /><PIcon name="car" /><PIcon name="car" size="lg" />
        <PIcon name="car" size="xl" />
        <PLogo /><PLogo size="sm" :animated="false" />
      </ShowcaseRow>
    </ShowcaseSection>

    <ShowcaseSection title="Botões">
      <ShowcaseRow label="variant">
        <PButton variant="primary">Salvar</PButton>
        <PButton>Cancelar</PButton>
        <PButton variant="tonal">Adicionar peça</PButton>
        <PButton variant="ghost">Ver detalhes</PButton>
        <PButton variant="danger">Excluir</PButton>
        <PButton variant="chip" icon="fuel" icon-tone="garage">Abastecer</PButton>
        <PButton variant="chip" icon="minus" icon-tone="finance">Despesa</PButton>
      </ShowcaseRow>
      <ShowcaseRow label="state · size">
        <PButton variant="primary" loading>Salvando</PButton>
        <PButton disabled>Desabilitado</PButton>
        <PButton variant="primary" size="lg">Entrar</PButton>
        <PButton icon="refresh" variant="primary">Tentar de novo</PButton>
        <PButton icon-right="chevron-down">Novembro</PButton>
      </ShowcaseRow>
      <ShowcaseRow label="dashed">
        <PButton variant="dashed" icon="add">Adicionar veículo</PButton>
      </ShowcaseRow>
      <ShowcaseRow label="icon · fab · link">
        <PIconButton icon="more" label="Mais ações" variant="outline" />
        <PIconButton icon="close" label="Fechar" />
        <PIconButton icon="search" label="Buscar" variant="tonal" />
        <PIconButton icon="add" label="Adicionar" variant="primary" size="sm" />
        <PFab icon="add" label="Registrar" />
        <PFab icon="add" label="Registrar" variant="floating" />
        <PLink href="#">Abrir</PLink>
      </ShowcaseRow>
    </ShowcaseSection>

    <ShowcaseSection title="Chips, badges e status">
      <ShowcaseRow>
        <PBadge>Moto</PBadge>
        <PBadge tone="garage">vence por km</PBadge>
        <PBadge tone="finance">Aberta</PBadge>
        <PBadge tone="reading">Lendo</PBadge>
        <PBadge tone="danger">Vencida</PBadge>
        <PBadge variant="solid">Editando</PBadge>
        <PBadge variant="outline">Quero ler</PBadge>
        <PBadge variant="dashed">Serviço</PBadge>
        <PBadge tone="garage" dot>Vence primeiro pela quilometragem</PBadge>
      </ShowcaseRow>
      <ShowcaseRow>
        <PBadge variant="tag">Kit relação · <b>R$ 189,90</b></PBadge>
        <PStatus tone="garage">Veículos</PStatus>
        <PStatus tone="finance">Finanças</PStatus>
        <PStatus tone="reading">Livros</PStatus>
        <PStatus>Neutro</PStatus>
        <PKbd>Ctrl K</PKbd>
      </ShowcaseRow>
    </ShowcaseSection>

    <ShowcaseSection title="Campos">
      <div class="showcase__fields">
        <PField label="Texto" hint="Dica abaixo do campo">
          <PInput v-model="text" />
        </PField>
        <PField label="Senha">
          <PInput v-model="password" type="password" icon="lock" revealable />
        </PField>
        <PField label="Dinheiro (centavos)" :hint="`Valor: ${cents} centavos`">
          <PMoneyInput v-model="cents" />
        </PField>
        <PField label="Valor em destaque" hint='size="lg"'>
          <PMoneyInput v-model="bigCents" size="lg" />
        </PField>
        <PField label="Calculado" hint="Fundo cinza e borda tracejada">
          <PInput model-value="6,35" prefix="R$" align="end" calculated readonly />
        </PField>
        <PField label="Com erro" error="Menor que o último registro (18.420 km em 17/11).">
          <PNumberInput v-model="km" suffix="km" />
        </PField>
        <PField label="Litros">
          <PNumberInput v-model="liters" :decimals="2" suffix="L" />
        </PField>
        <PField label="Desabilitado">
          <PInput model-value="henrique" disabled />
        </PField>
        <PField label="Observações" optional>
          <PTextarea v-model="notes" placeholder="Algo que valha lembrar na próxima visita" />
        </PField>
        <PField label="Data">
          <PDateInput v-model="date" />
        </PField>
        <PField label="Hora">
          <PDateInput v-model="time" type="time" />
        </PField>
      </div>
    </ShowcaseSection>

    <ShowcaseSection title="Seleção">
      <div class="showcase__fields">
        <PField label="Seleção">
          <PSelect v-model="account" :options="accounts" :portal="false" />
        </PField>
        <PField label="Filtro" label-as="span">
          <PSelect
            v-model="account"
            :options="accounts"
            :portal="false"
            variant="filter"
            icon="calendar"
          />
        </PField>
        <PField label="Busca com criação">
          <PCombobox
            v-model="workshop"
            :options="workshops"
            placeholder="Oficina"
            :create-label="(term) => `Cadastrar nova oficina “${term}”`"
            :portal="false"
          />
        </PField>
        <PField label="Escolha única" label-as="span">
          <PSegmented v-model="kind" :options="kinds" label="Tipo" />
        </PField>
        <PField label="Liga e desliga" label-as="span">
          <div class="showcase__inline">
            <PSwitch v-model="on" label="Ligado" />
            <PSwitch v-model="off" label="Desligado" />
            <PSwitch :model-value="true" label="Desabilitado" disabled />
            <PCheckbox v-model="checked">Caixa</PCheckbox>
          </div>
        </PField>
        <PField label="Cor" label-as="span">
          <PSwatchPicker v-model="color" :options="swatches" label="Cor" />
        </PField>
        <PField label="Ícone" label-as="span">
          <PIconPicker
            v-model="pickedIcon"
            :options="iconChoices"
            label="Ícone"
            :tone="`swatch-${color}`"
          />
        </PField>
        <PField label="Chips com ícone" label-as="span">
          <PChipChoice v-model="chip" :options="chips" label="Categoria" tone="finance" />
        </PField>
        <PField label="Arquivo" label-as="span">
          <PFileButton accept="image/*" @select="(file) => toast.show({ title: file.name })"
            >Enviar imagem</PFileButton
          >
        </PField>
        <PField label="Mês" label-as="span">
          <PMonthNav v-model="month" label="Mês" />
        </PField>
        <PField label="Página atual" label-as="span">
          <div class="showcase__inline">
            <PStepper v-model="page" prefix="p." :max="425" label="Página atual" />
            <PButton variant="primary">Salvar</PButton>
          </div>
        </PField>
      </div>
      <PChoiceCards v-model="themeChoice" :options="themes" label="Tema">
        <template #preview="{ option }"><PThemePreview :theme="option.value" /></template>
      </PChoiceCards>
    </ShowcaseSection>

    <ShowcaseSection title="Cards, listas e tabelas">
      <PCard
        variant="flat"
        padding="sm"
        density="tight"
        title="Título do módulo"
        subtitle="Subtítulo"
        icon="car"
        tone="garage"
        link-label="Abrir"
        :to="{ path: '/dev/ui' }"
        :heading-level="3"
      >
        <PList>
          <PListItem title="Item de lista com data">
            <template #leading><PDateBadge date="2026-11-25" /><PStatus tone="garage" /></template>
          </PListItem>
          <PListItem title="Item com ícone" subtitle="Ontem, 11:25 · Nubank">
            <template #leading><PTile icon="minus" tone="finance" /></template>
            <template #trailing><PText variant="h3" as="span">R$ 212,40</PText></template>
          </PListItem>
          <PListItem title="Item em edição" subtitle="current" current>
            <template #leading><PTile icon="fuel" tone="swatch-gray" /></template>
            <template #trailing><PBadge variant="solid">Editando</PBadge></template>
          </PListItem>
        </PList>
      </PCard>
      <PTable :columns="columns" :rows="rows" :row-key="(row) => row.id" caption="Exemplo">
        <template #cell-amount="{ row }">
          <PText variant="h3" as="span" :tone="row.amount > 0 ? 'success' : 'default'"
            >{{ row.amount > 0 ? '+' : '−' }} R$ {{ moneyAmount(row.amount) }}</PText
          >
        </template>
      </PTable>
      <div class="showcase__stats">
        <PStatCard label="Indicador" value="R$ 271,04" caption="contexto" variant="flat" />
        <PStatCard
          label="Resultado do mês"
          value="+ R$ 2.735,81"
          caption="até 17/11"
          value-tone="success"
        />
        <PDescriptionList
          :items="[
            { label: 'Rótulo', value: 'Valor' },
            { label: 'Intervalo', value: '1.000 km' },
          ]"
        />
      </div>
      <ShowcaseRow label="book cover">
        <PBookCover title="Código Limpo" author="Robert C. Martin" size="lg" />
        <PBookCover title="O Hobbit" author="J.R.R. Tolkien" variant="paper" />
        <PBookCover title="Dom Casmurro" author="Machado de Assis" variant="ink" />
        <PBookCover title="Código Limpo" size="sm" />
      </ShowcaseRow>
      <div class="showcase__card-face">
        <PCardFace name="Nubank" caption="Fecha dia 3 · vence dia 10" tone="swatch-green" />
      </div>
      <ShowcaseRow label="tile · avatar">
        <PTile icon="car" tone="garage" />
        <PTile icon="wallet" tone="finance" />
        <PTile icon="book" tone="reading" />
        <PTile icon="trash" tone="danger" />
        <PTile icon="modules" />
        <PTile icon="car" tone="garage" size="lg" />
        <PTile icon="book" tone="reading" size="xl" />
        <PAvatar name="Henrique Sebastião" />
        <PAvatar name="Henrique Sebastião" size="lg" />
      </ShowcaseRow>
      <PSortableList
        v-model="sortable"
        :item-key="(item) => item.id"
        :item-label="(item) => item.label"
        label="Ordem"
      >
        <template #default="{ item }">
          <PTile
            :icon="item.id === 'finance' ? 'wallet' : item.id === 'garage' ? 'car' : 'book'"
            :tone="item.id"
          />
          <PText variant="h3" as="span" class="showcase__grow">{{ item.label }}</PText>
          <PSwitch :model-value="true" :label="item.label" />
        </template>
      </PSortableList>
    </ShowcaseSection>

    <ShowcaseSection title="Progresso e gráficos">
      <div class="showcase__inline">
        <PRing :value="78" tone="garage" :size="96">
          <PText variant="number-l" as="span">220</PText>
          <PText variant="xs" tone="muted" as="span">km</PText>
        </PRing>
        <PRing :value="50" tone="reading" :size="72"
          ><PText variant="sm" weight="bold" as="span">50%</PText></PRing
        >
        <PRing :value="29" :size="72"><PText variant="sm" weight="bold" as="span">65</PText></PRing>
        <div class="showcase__bars">
          <PProgress :value="78" tone="garage" />
          <PProgress :value="48" tone="finance" strong />
          <PProgress :value="50" tone="reading" />
          <PProgress :value="29" size="sm" />
          <PProgress :value="95" tone="danger" size="lg" />
        </div>
      </div>
      <PChart
        type="bars"
        label="Consumo médio dos últimos 5 tanques cheios"
        tone="garage"
        :data="[
          { label: '07/10', value: 41.2 },
          { label: '17/10', value: 40.1 },
          { label: '27/10', value: 39.9 },
          { label: '06/11', value: 40.6 },
          { label: '16/11', value: 40.1, highlight: true },
        ]"
        :domain="[38, 42]"
        :average="{ value: 40.4, label: 'média 40,4' }"
        value-labels="all"
        :format="(v) => v.toLocaleString('pt-BR', { minimumFractionDigits: 1 })"
      />
      <PChart
        type="grouped"
        label="Receitas e despesas por mês"
        tone="finance"
        :series="['Receitas', 'Despesas']"
        :data="[
          { label: 'set', values: [5800, 3100] },
          { label: 'out', values: [5200, 2900] },
          { label: 'nov', values: [5300, 2600], highlight: true },
        ]"
        value-labels="highlight"
        :format="(v) => `${(v / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mil`"
      />
      <PChart
        type="donut"
        label="Despesas por categoria"
        tone="finance"
        legend
        :height="140"
        :data="[
          { label: 'Moradia', value: 138630 },
          { label: 'Alimentação', value: 74285 },
          { label: 'Combustível', value: 27104 },
          { label: 'Lazer', value: 16400 },
        ]"
        :format="moneyAmount"
      >
        <template #center>
          <PText variant="xs" tone="muted" as="span">Total</PText>
          <PText variant="h3" as="span">2.564,19</PText>
        </template>
      </PChart>
      <PChart
        type="stacked"
        label="Gastos por categoria"
        tone="finance"
        legend
        :data="[
          { label: 'Moradia', value: 138630 },
          { label: 'Alimentação', value: 74285 },
          { label: 'Combustível', value: 27104 },
          { label: 'Lazer', value: 16400 },
        ]"
        :format="moneyAmount"
      />
    </ShowcaseSection>

    <ShowcaseSection title="Navegação">
      <PPageHeader overline="Finanças" title="Visão geral">
        <PButton variant="primary" icon="add">Nova transação</PButton>
      </PPageHeader>
      <PPageHeader
        title="Honda CG 160 Fan"
        :back="{ label: 'Veículos', to: '/dev/ui' }"
        size="sm"
      />
      <PTabs
        v-model="tab"
        label="Histórico"
        :items="[
          { value: 'maintenances', label: 'Manutenções', count: 3 },
          { value: 'fuelings', label: 'Abastecimentos', count: 14 },
        ]"
      >
        <PTabPanel value="maintenances"
          ><PText variant="sm" tone="muted">Painel de manutenções</PText></PTabPanel
        >
        <PTabPanel value="fuelings"
          ><PText variant="sm" tone="muted">Painel de abastecimentos</PText></PTabPanel
        >
      </PTabs>
      <PTabs
        mode="nav"
        label="Seções"
        model-value="overview"
        :items="[
          { value: 'overview', label: 'Visão geral', to: '/dev/ui' },
          { value: 'transactions', label: 'Transações', to: '/dev/ui' },
          { value: 'accounts', label: 'Contas', to: '/dev/ui' },
        ]"
      />
      <PSearchField placeholder="Buscar no Prumo" as="button" shortcut="Ctrl K" />
      <PNavList
        label="Seções"
        :items="[
          { key: 'p', label: 'Perfil', icon: 'user', current: true, to: '/dev/ui' },
          { key: 'a', label: 'Aparência', icon: 'appearance', to: '/dev/ui' },
          { type: 'separator' },
          { key: 's', label: 'Sair', icon: 'logout', danger: true },
        ]"
      />
    </ShowcaseSection>

    <ShowcaseSection
      title="Diálogos, menus e popovers"
      note="Diálogos em modo inline aqui; na aplicação abrem com fundo escurecido e foco preso."
    >
      <div class="showcase__scrim">
        <PDialog title="Diálogo" size="s" inline>
          <PText variant="sm" tone="secondary"
            >Cabeçalho, corpo e rodapé com ações à direita.</PText
          >
          <template #footer><PButton variant="primary">Salvar</PButton></template>
        </PDialog>
        <PConfirmDialog
          title="Excluir abastecimento?"
          description="O abastecimento de 16/11/2026 (7,30 L · R$ 46,36) será excluído e o consumo médio, recalculado. Não dá para desfazer."
          confirm-label="Excluir"
          inline
        />
        <div class="showcase__menu p-menu">
          <PCommand
            :groups="commandGroups"
            placeholder="O que você quer registrar?"
            empty-label="Nada encontrado."
          />
        </div>
      </div>
      <ShowcaseRow label="interactive">
        <PButton @click="dialogOpen = true">Abrir diálogo</PButton>
        <PButton @click="drawerOpen = true">Abrir gaveta</PButton>
        <PPopover v-model:open="popoverOpen" :portal="false" label="Atualizar km">
          <template #trigger><PButton icon="gauge" icon-tone="garage">Popover</PButton></template>
          <PField label="Km atual"><PNumberInput v-model="km" suffix="km" /></PField>
          <PButton variant="primary" @click="popoverOpen = false">Salvar</PButton>
        </PPopover>
        <PMenu :items="menuItems" :portal="false">
          <template #trigger><PIconButton icon="more" label="Menu" variant="outline" /></template>
        </PMenu>
        <PButton @click="toast.show({ title: 'Alterações salvas' })">Mostrar toast</PButton>
      </ShowcaseRow>
      <PDialog v-model:open="dialogOpen" title="Atualizar km">
        <PField label="Km atual"><PNumberInput v-model="km" suffix="km" /></PField>
        <template #footer>
          <PButton @click="dialogOpen = false">Cancelar</PButton>
          <PButton variant="primary" @click="dialogOpen = false">Salvar</PButton>
        </template>
      </PDialog>
      <PDrawer v-model:open="drawerOpen" title="Mais">
        <PText>Conteúdo da gaveta (celular).</PText>
      </PDrawer>
    </ShowcaseSection>

    <ShowcaseSection title="Estados">
      <PEmptyState
        icon="car"
        tone="garage"
        title="Nenhum veículo ainda"
        description="Cadastre seu carro ou moto para acompanhar km, abastecimentos e trocas de óleo."
      >
        <PButton variant="primary" icon="add">Cadastrar veículo</PButton>
      </PEmptyState>
      <PDivider />
      <PQueryState :loading="true" />
      <PDivider />
      <PQueryState
        :loading="false"
        :error="networkError"
        error-title="Não foi possível carregar as transações"
      />
      <PDivider />
      <div class="showcase__inline">
        <PSkeleton shape="tile" width="40px" height="40px" />
        <span class="showcase__grow showcase__lines">
          <PSkeleton width="60%" />
          <PSkeleton width="35%" height="10px" />
        </span>
        <PSpinner label="Carregando" />
      </div>
      <PAlert title="Alerta de erro" description="Com descrição e ações ao lado." />
      <PNote>Nota informativa, neutra.</PNote>
    </ShowcaseSection>
  </div>
</template>

<style scoped>
.showcase {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.showcase__tokens {
  display: grid;
  gap: var(--space-2);
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.showcase__token {
  display: flex;
  align-items: center;
  gap: var(--space-2-5);
}

.showcase__token code,
.showcase__tone code {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

.showcase__card-face {
  max-width: 360px;
}

.showcase__swatch {
  width: 36px;
  height: 36px;
  flex: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.showcase__tone {
  display: inline-flex;
  align-items: center;
  gap: var(--space-0-5);
}

.showcase__tone i {
  width: 18px;
  height: 18px;
  border-radius: var(--radius-xs);
}

.showcase__tone i:nth-child(1) {
  background: var(--tone);
}

.showcase__tone i:nth-child(2) {
  background: var(--tone-container);
}

.showcase__tone i:nth-child(3) {
  background: var(--tone-on-container);
}

.showcase__tone i:nth-child(4) {
  background: var(--tone-soft);
}

.showcase__tone i:nth-child(5) {
  margin-right: var(--space-1);
  background: var(--tone-softer);
}

.showcase__icons {
  display: grid;
  gap: var(--space-2);
  grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
}

.showcase__icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  background: var(--color-surface-inset);
  text-align: center;
}

.showcase__fields {
  display: grid;
  gap: var(--space-4-5) var(--space-5);
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
}

.showcase__inline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
}

.showcase__bars {
  display: flex;
  min-width: 160px;
  flex: 1;
  flex-direction: column;
  gap: var(--space-2-5);
}

.showcase__stats {
  display: grid;
  gap: var(--space-3);
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.showcase__grow {
  flex: 1;
}

.showcase__lines {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.showcase__scrim {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-5);
  border-radius: var(--radius-menu);
  background: var(--color-scrim);
}

.showcase__scrim > :deep(.p-dialog) {
  max-width: 320px;
}

.showcase__menu {
  width: 300px;
}
</style>
