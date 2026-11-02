<script setup lang="ts">
/**
 * Design v1 "Início", rebuilt with src/ui only and fake data (dev only). Used to compare the
 * component library with design/v1/ by screenshot and to validate a redesign; the real Início
 * gets the same blocks from the modules' widgets.
 */
import { ref } from 'vue'

import NavRail from '@/layouts/NavRail.vue'
import type { NavItem } from '@/layouts/nav'
import {
  PBadge,
  PButton,
  PCard,
  PChart,
  PDateBadge,
  PIcon,
  PList,
  PListItem,
  PPageHeader,
  PPanel,
  PProgress,
  PRing,
  PSearchField,
  PStatus,
  PStepper,
  PText,
  PTile,
} from '@/ui'
import { moneyAmount } from '@/lib/format'

defineProps<{ compact?: boolean }>()

const page = ref(212)
const nav: NavItem[] = [
  { key: 'home', label: 'Início', icon: 'home', to: '/dev/ui', current: true },
  { key: 'garage', label: 'Veículos', icon: 'car', to: '/dev/ui', tone: 'garage', current: false },
  {
    key: 'finance',
    label: 'Finanças',
    icon: 'wallet',
    to: '/dev/ui',
    tone: 'finance',
    current: false,
  },
  { key: 'reading', label: 'Livros', icon: 'book', to: '/dev/ui', tone: 'reading', current: false },
  { key: 'modules', label: 'Módulos', icon: 'modules', to: '/dev/ui', current: false },
]
const chips = [
  { label: 'Abastecer', icon: 'fuel', tone: 'garage' },
  { label: 'Atualizar km', icon: 'gauge', tone: 'garage' },
  { label: 'Despesa', icon: 'minus', tone: 'finance' },
  { label: 'Receita', icon: 'add', tone: 'finance' },
  { label: 'Transferência', icon: 'transfer', tone: 'finance' },
  { label: 'Página lida', icon: 'bookmark', tone: 'reading' },
] as const
const categories = [
  { label: 'Moradia', value: 138630 },
  { label: 'Alimentação', value: 74285 },
  { label: 'Combustível', value: 27104 },
  { label: 'Lazer', value: 16400 },
]
</script>

<template>
  <div class="home-demo">
    <NavRail :items="nav" :sections="[]" />
    <main class="home-demo__main">
      <PPageHeader overline="Terça, 17 de novembro de 2026" title="Boa tarde, Henrique">
        <PSearchField as="button" placeholder="Buscar no Prumo" shortcut="Ctrl K" />
      </PPageHeader>

      <div class="home-demo__chips">
        <PButton
          v-for="chip in chips"
          :key="chip.label"
          variant="chip"
          :icon="chip.icon"
          :icon-tone="chip.tone"
          >{{ chip.label }}</PButton
        >
      </div>

      <div class="home-demo__grid">
        <PCard
          as="article"
          title="Veículos"
          subtitle="2 veículos"
          icon="car"
          tone="garage"
          link-label="Abrir"
          to="/dev/ui"
        >
          <PPanel class="home-demo__row home-demo__row--nowrap">
            <PRing :value="78" tone="garage" :size="92">
              <PText variant="number-l" as="span">220</PText>
              <PText variant="xs" tone="muted" weight="bold" as="span">km</PText>
            </PRing>
            <div class="home-demo__stack-xs">
              <PText variant="sm" tone="muted">Próxima troca de óleo</PText>
              <PText variant="strong">Honda CG 160 Fan</PText>
              <PText variant="sm" tone="secondary">≈ 8 dias · por volta de 25/11</PText>
            </div>
          </PPanel>
          <PList>
            <PListItem title="Honda CG 160 Fan" subtitle="18.420 km · óleo por km">
              <template #trailing>
                <PProgress :value="78" tone="garage" size="sm" class="home-demo__mini-bar" />
                <PText variant="h3" as="span" class="home-demo__value">220 km</PText>
              </template>
            </PListItem>
            <PListItem title="Fiat Strada Freedom" subtitle="52.300 km · óleo por data">
              <template #trailing>
                <PProgress :value="95" tone="garage" size="sm" class="home-demo__mini-bar" />
                <PText variant="h3" as="span" class="home-demo__value">18 dias</PText>
              </template>
            </PListItem>
          </PList>
          <div class="home-demo__between">
            <PText variant="sm" tone="muted">Combustível em novembro</PText>
            <PText variant="h3">R$ 271,04</PText>
          </div>
          <div class="home-demo__row">
            <PButton variant="primary" class="home-demo__grow">Atualizar km</PButton>
            <PButton class="home-demo__grow">Abastecer</PButton>
          </div>
        </PCard>

        <PCard
          as="article"
          title="Finanças"
          subtitle="Novembro de 2026"
          icon="wallet"
          tone="finance"
          link-label="Abrir"
          to="/dev/ui"
        >
          <div class="home-demo__stack-xs">
            <PText variant="sm" tone="muted">Saldo total</PText>
            <PText variant="number-xl"><small>R$</small> 7.154,27</PText>
          </div>
          <div class="home-demo__accounts">
            <PPanel
              v-for="[name, value] in [
                ['Nubank', '4.812,37'],
                ['Inter', '2.156,90'],
                ['Carteira', '185,00'],
              ]"
              :key="name"
              padding="sm"
            >
              <PText variant="xs" tone="muted">{{ name }}</PText>
              <PText variant="h3">{{ value }}</PText>
            </PPanel>
          </div>
          <div class="home-demo__stack-s">
            <div class="home-demo__between">
              <PText variant="sm" tone="secondary">Receitas</PText>
              <PText variant="sm" weight="bold">R$ 5.300,00</PText>
            </div>
            <PProgress :value="100" tone="finance" label="Receitas" />
            <div class="home-demo__between">
              <PText variant="sm" tone="secondary">Gastos · 48%</PText>
              <PText variant="sm" weight="bold">R$ 2.564,19</PText>
            </div>
            <PProgress :value="48" tone="finance" strong label="Gastos" />
          </div>
          <div class="home-demo__stack-s">
            <PText variant="sm" tone="muted">Gastos por categoria</PText>
            <PChart
              type="stacked"
              tone="finance"
              label="Gastos por categoria"
              legend
              :data="categories"
              :format="moneyAmount"
            />
          </div>
          <PPanel padding="sm" class="home-demo__row home-demo__row--nowrap">
            <PIcon name="card" data-tone="finance" />
            <PText variant="sm" class="home-demo__grow">Fatura Nubank</PText>
            <PText variant="sm" weight="bold">R$ 1.284,60</PText>
            <PText variant="sm" tone="muted">· vence 10/12</PText>
          </PPanel>
        </PCard>

        <PCard
          as="article"
          title="Livros"
          subtitle="3 na estante"
          icon="book"
          tone="reading"
          link-label="Abrir"
          to="/dev/ui"
        >
          <div class="home-demo__row home-demo__row--nowrap home-demo__row--top">
            <PPanel tone="reading" padding="sm" class="home-demo__cover">
              <PText variant="sm" weight="bold">Código Limpo</PText>
              <PText variant="xs" weight="semibold">Robert C. Martin</PText>
            </PPanel>
            <div class="home-demo__stack-s home-demo__grow">
              <div class="home-demo__stack-xs">
                <PText variant="sm" tone="muted">Lendo agora</PText>
                <PText variant="h2">Código Limpo</PText>
                <PText variant="sm" tone="secondary">Robert C. Martin</PText>
              </div>
              <div class="home-demo__between">
                <PText variant="sm" tone="secondary">p. 212 de 425</PText>
                <PText variant="sm" weight="bold">50%</PText>
              </div>
              <PProgress :value="50" tone="reading" label="Progresso" />
            </div>
          </div>
          <div class="home-demo__row home-demo__row--nowrap">
            <PStepper v-model="page" prefix="p." :max="425" label="Página atual" />
            <PButton variant="primary">Salvar</PButton>
          </div>
          <PList>
            <PListItem title="Dom Casmurro" subtitle="Machado de Assis">
              <template #trailing><PBadge>Lido · 18/10</PBadge></template>
            </PListItem>
            <PListItem title="O Hobbit" subtitle="J.R.R. Tolkien · 336 p.">
              <template #trailing><PBadge variant="outline">Quero ler</PBadge></template>
            </PListItem>
          </PList>
        </PCard>
      </div>

      <div class="home-demo__split">
        <PCard as="section" title="Vem aí" class="home-demo__half">
          <PList>
            <PListItem
              v-for="item in [
                {
                  date: '2026-11-25',
                  tone: 'garage',
                  title: 'Troca de óleo · CG 160 Fan',
                  text: 'Estimativa pelo ritmo de 29 km/dia',
                },
                {
                  date: '2026-12-03',
                  tone: 'finance',
                  title: 'Fatura Nubank fecha',
                  text: 'Limite disponível R$ 3.715,40',
                },
                {
                  date: '2026-12-05',
                  tone: 'garage',
                  title: 'Troca de óleo · Strada',
                  text: 'Vence por data (12 meses)',
                },
                {
                  date: '2026-12-10',
                  tone: 'finance',
                  title: 'Fatura Nubank vence',
                  text: 'R$ 1.284,60 até agora',
                },
              ]"
              :key="item.title"
              :title="item.title"
              :subtitle="item.text"
            >
              <template #leading
                ><PDateBadge :date="item.date" /><PStatus :tone="item.tone"
              /></template>
            </PListItem>
          </PList>
        </PCard>
        <PCard
          as="section"
          title="Atividade recente"
          link-label="Ver tudo"
          to="/dev/ui"
          class="home-demo__half"
        >
          <PList>
            <PListItem title="Km atualizado · CG 160 Fan" subtitle="Hoje, 07:42">
              <template #leading><PTile icon="gauge" tone="garage" shape="circle" /></template>
              <template #trailing><PText variant="strong" as="span">18.420 km</PText></template>
            </PListItem>
            <PListItem title="Abastecimento · CG 160 Fan" subtitle="Ontem, 18:10 · 7,30 L">
              <template #leading><PTile icon="fuel" tone="garage" shape="circle" /></template>
              <template #trailing><PText variant="strong" as="span">R$ 46,36</PText></template>
            </PListItem>
            <PListItem title="Supermercado · Alimentação" subtitle="Ontem, 11:25 · Nubank">
              <template #leading><PTile icon="minus" tone="finance" shape="circle" /></template>
              <template #trailing><PText variant="strong" as="span">− R$ 212,40</PText></template>
            </PListItem>
            <PListItem title="Leitura · Código Limpo" subtitle="15/11, 22:05 · até a página 212">
              <template #leading><PTile icon="bookmark" tone="reading" shape="circle" /></template>
              <template #trailing><PText variant="strong" as="span">+14 p.</PText></template>
            </PListItem>
          </PList>
        </PCard>
      </div>
    </main>
  </div>
</template>

<style scoped>
.home-demo {
  display: flex;
  min-height: 100vh;
}

.home-demo__main {
  display: flex;
  min-width: 0;
  max-width: var(--page-max-width);
  flex: 1;
  flex-direction: column;
  gap: var(--space-5);
  margin: 0 auto;
  padding: var(--space-6-5) var(--space-8) var(--space-12) var(--space-2);
}

.home-demo__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.home-demo__grid {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr));
}

.home-demo__split {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: var(--space-4);
}

.home-demo__half {
  min-width: 0;
  flex: 1 1 420px;
}

.home-demo__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.home-demo__row--nowrap {
  flex-wrap: nowrap;
  gap: var(--space-4);
}

.home-demo__row--top {
  align-items: stretch;
}

.home-demo__between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.home-demo__stack-xs {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-0-5);
}

.home-demo__stack-s {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-2);
}

.home-demo__grow {
  min-width: 0;
  flex: 1;
}

.home-demo__accounts {
  display: grid;
  gap: var(--space-2);
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.home-demo__mini-bar {
  width: 100px;
}

.home-demo__value {
  min-width: 64px;
  text-align: right;
}

.home-demo__cover {
  display: flex;
  width: 72px;
  flex: none;
  flex-direction: column;
  justify-content: space-between;
}
</style>
