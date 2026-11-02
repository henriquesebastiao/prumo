<script setup lang="ts">
/** Design v1 "Estados da interface", rebuilt with src/ui only (dev only). */
import { ref } from 'vue'

import { ApiError } from '@/lib/api/errors'
import {
  PButton,
  PCard,
  PConfirmDialog,
  PDivider,
  PEmptyState,
  PField,
  PNumberInput,
  PPageHeader,
  PPanel,
  PQueryState,
  PSkeleton,
  PText,
} from '@/ui'

const km = ref<number | null>(18300)
const networkError = ApiError.network(new Error('offline'))
</script>

<template>
  <div class="states-demo">
    <PPageHeader
      overline="Padrões reaproveitados por todos os módulos"
      title="Estados da interface"
    />

    <PText as="h2" variant="h2">Primeiro uso — estados vazios</PText>
    <div class="states-demo__grid">
      <PCard>
        <PEmptyState
          icon="car"
          tone="garage"
          title="Nenhum veículo ainda"
          description="Cadastre seu carro ou moto para acompanhar km, abastecimentos e trocas de óleo."
        >
          <PButton variant="primary" icon="add">Cadastrar veículo</PButton>
        </PEmptyState>
      </PCard>
      <PCard>
        <PEmptyState
          icon="wallet"
          tone="finance"
          title="Comece pelas suas contas"
          description="Adicione suas contas e a carteira com o saldo de hoje. As transações vêm depois."
        >
          <PButton variant="primary" icon="add">Adicionar conta</PButton>
          <PButton>Usar categorias sugeridas</PButton>
        </PEmptyState>
      </PCard>
      <PCard>
        <PEmptyState
          icon="book"
          tone="reading"
          title="Sua estante está vazia"
          description="Adicione o livro que está lendo agora e acompanhe o progresso página a página."
        >
          <PButton variant="primary" icon="add">Adicionar livro</PButton>
        </PEmptyState>
      </PCard>
    </div>

    <div class="states-demo__grid">
      <section class="states-demo__column">
        <PText as="h2" variant="h2">Carregando</PText>
        <PCard>
          <PQueryState :loading="true">
            <template #loading>
              <div class="states-demo__row">
                <PSkeleton shape="tile" width="40px" height="40px" />
                <span class="states-demo__lines">
                  <PSkeleton width="40%" height="14px" />
                  <PSkeleton width="24%" height="10px" />
                </span>
              </div>
              <PPanel class="states-demo__row">
                <PSkeleton shape="circle" width="92px" height="92px" />
                <span class="states-demo__lines">
                  <PSkeleton width="50%" height="10px" />
                  <PSkeleton width="80%" height="14px" />
                  <PSkeleton width="60%" height="10px" />
                </span>
              </PPanel>
              <span class="states-demo__lines">
                <PSkeleton height="12px" />
                <PSkeleton width="70%" height="12px" />
              </span>
            </template>
          </PQueryState>
        </PCard>
      </section>
      <section class="states-demo__column">
        <PText as="h2" variant="h2">Erro</PText>
        <PCard>
          <PQueryState
            :loading="false"
            :error="networkError"
            error-title="Não foi possível carregar as transações"
          />
          <PDivider />
          <PText variant="sm" weight="bold" tone="secondary">Erro de validação em formulário</PText>
          <PField
            label="Km atual"
            error="Menor que o último registro (18.420 km em 17/11). Confira o valor."
          >
            <PNumberInput v-model="km" suffix="km" />
          </PField>
        </PCard>
      </section>
      <section class="states-demo__column">
        <PText as="h2" variant="h2">Confirmação de exclusão</PText>
        <div class="states-demo__scrim">
          <PConfirmDialog
            inline
            title="Excluir abastecimento?"
            description="O abastecimento de 16/11/2026 (7,30 L · R$ 46,36) da Honda CG 160 Fan será excluído e o consumo médio, recalculado. Não dá para desfazer."
            confirm-label="Excluir"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.states-demo {
  display: flex;
  max-width: 1320px;
  flex-direction: column;
  gap: var(--space-6);
  margin: 0 auto;
  padding: var(--space-10) var(--space-10) var(--space-14);
}

.states-demo__grid {
  display: grid;
  align-items: start;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(360px, 100%), 1fr));
}

.states-demo__column {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.states-demo__row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.states-demo__lines {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--space-2);
}

.states-demo__scrim {
  padding: var(--space-7);
  border-radius: var(--radius-xl);
  background: var(--color-scrim);
}
</style>
