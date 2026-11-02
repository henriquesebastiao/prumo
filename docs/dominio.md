# Domínio e regras de negócio

Este documento é a fonte de verdade para regras de negócio. Em caso de conflito com o design, as regras daqui prevalecem e o design prevalece na apresentação. Conflitos devem ser apontados, não resolvidos em silêncio.

Convenções de todas as entidades: `id` (UUID v7), `created_at`, `updated_at`; entidades de usuário têm `user_id`. Os campos abaixo omitem esses.

## Sistema

**User**: `username` (único), `display_name`, `password_hash`, `is_admin`.

**Session**: `token_hash`, `client` (`web` | `app`), `device_name`, `last_used_at`, `expires_at`, `revoked_at`.

**Preferences** (1:1 com User): `theme` (`system` | `light` | `dark`), `locale` (`pt-BR`), `timezone` (padrão da instância), `currency` (padrão `BRL`), `enabled_modules` (lista ordenada de ids; padrão: todos os instalados).

Regras:
- S1. Não há cadastro público. Usuários são criados pela CLI; ao criar, executa-se o `on_user_created` de cada módulo.
- S2. Usuários não compartilham dados entre si.
- S3. "Hoje", "este mês" e "data de um registro" são sempre calculados no fuso da preferência do usuário.

## Veículos (`garage`)

**Vehicle**: `kind` (`car` | `motorcycle`), `name` (apelido exibido), `brand`, `model`, `year`, `current_km`, `oil_interval_km?`, `oil_interval_months?`, `notes?`, `archived_at?`.

**OdometerReading**: `vehicle_id`, `km`, `recorded_at`, `source` (`manual` | `maintenance` | `fueling`), `source_id?`.

**Workshop**: `name` (único por usuário, sem diferenciar maiúsculas), `notes?`.

**Maintenance**: `vehicle_id`, `kind` (`general` | `oil_change`), `performed_at`, `km`, `workshop_id?`, `labor_cost_cents`, `notes?`, `next_oil_change_km?`, `next_oil_change_on?` (os dois últimos só em `oil_change`).

**MaintenanceItem**: `maintenance_id`, `description`, `quantity` (inteiro ≥ 1), `unit_price_cents`.

**Fueling**: `vehicle_id`, `fueled_at`, `km`, `fuel_type`, `volume_ml`, `total_cents`, `full_tank` (bool), `notes?`.

`fuel_type`: `gasoline` (Gasolina comum), `gasoline_additive` (Gasolina aditivada), `gasoline_premium` (Gasolina premium), `ethanol` (Etanol), `diesel` (Diesel), `cng` (GNV).

Regras:
- G1. Intervalos de troca de óleo são opcionais. Sem nenhum, o veículo não exibe status de óleo.
- G2. Odômetro. Todo registro com km (cadastro do veículo, leitura manual, manutenção, abastecimento) gera uma `OdometerReading`. `current_km` é o km da leitura mais recente no tempo.
- G3. Consistência cronológica. Uma leitura não pode ser menor que outra leitura anterior no tempo nem maior que outra posterior; caso contrário, `422 garage.odometer_inconsistent` com a leitura conflitante em `details`. Editar ou excluir um registro atualiza a leitura correspondente e recalcula `current_km`.
- G4. Total da manutenção = `labor_cost_cents` + Σ(`quantity` × `unit_price_cents`). Calculado pelo backend e retornado como `total_cents`.
- G5. Troca de óleo é uma manutenção com `kind = oil_change` (tem oficina, peças e mão de obra como qualquer manutenção). Ao registrá-la, o backend sugere `next_oil_change_km = km + oil_interval_km` e `next_oil_change_on = data + oil_interval_months`; o cliente pode alterar os dois valores.
- G6. Status de óleo, a partir da troca de óleo mais recente:
  - `remaining_km = next_oil_change_km − current_km`; `remaining_days = next_oil_change_on − hoje`.
  - `overdue` se qualquer um for ≤ 0; `due_soon` se `remaining_km` ≤ 10% do intervalo em km ou `remaining_days` ≤ 15; senão `ok`; sem troca registrada, `unknown`.
  - `primary` indica o critério que vence primeiro, ou seja, o de menor fração restante (`remaining / intervalo`). É o que a interface destaca.
- G7. Preço por litro (R$) = (`total_cents` ÷ 100) ÷ (`volume_ml` ÷ 1000), com 3 casas decimais, só para exibição.
- G8. Consumo pelo método do tanque cheio. Entre dois abastecimentos com `full_tank`, consumo = (km do atual − km do cheio anterior) ÷ (litros de todos os abastecimentos depois do cheio anterior até o atual, inclusive). O primeiro tanque cheio não gera consumo. `last_consumption_km_l` é o último ciclo; `avg_consumption_km_l` = Σkm ÷ Σlitros de todos os ciclos.
- G9. Gasto do mês do veículo = Σ totais de manutenções + Σ totais de abastecimentos no mês.
- G10. Oficinas: a manutenção aceita `workshop_id` ou `workshop_name`; um nome inexistente cria a oficina.
- G11. Veículo é arquivado por padrão. Exclusão definitiva apaga todo o histórico e exige confirmação explícita no cliente.

## Finanças (`finance`)

**Account**: `name`, `kind` (`checking` | `savings` | `cash` | `investment` | `other`), `initial_balance_cents` (pode ser negativo), `color`, `icon`, `include_in_total` (bool), `archived_at?`.

**Category**: `kind` (`income` | `expense`), `name` (único por usuário e `kind`), `color`, `icon`, `archived_at?`.

**CreditCard**: `name`, `limit_cents`, `closing_day` (1–31), `due_day` (1–31), `payment_account_id?`, `color`, `archived_at?`.

**Transaction**: `kind`, `amount_cents` (> 0), `occurred_on` (data), `description`, `notes?`, `account_id?`, `destination_account_id?`, `credit_card_id?`, `category_id?`, `invoice_closing_on?`.

Combinações válidas por `kind`:

| kind | account_id | destination_account_id | credit_card_id | category_id |
|---|---|---|---|---|
| `income` | obrigatório | — | — | obrigatório (receita) |
| `expense` na conta | obrigatório | — | — | obrigatório (despesa) |
| `expense` no cartão | — | — | obrigatório | obrigatório (despesa) |
| `transfer` | obrigatório (origem) | obrigatório (≠ origem) | — | — |
| `card_payment` | obrigatório | — | obrigatório | — |

Regras:
- F1. Saldo da conta = inicial + receitas − despesas − transferências enviadas + transferências recebidas − pagamentos de fatura. Calculado, não armazenado.
- F2. Saldo total = soma das contas não arquivadas com `include_in_total`.
- F3. Relatórios usam competência: despesa no cartão conta na data da compra. Pagamento de fatura nunca é despesa nem entra em relatórios por categoria (evita contar duas vezes).
- F4. Fatura de uma compra no cartão:
  - A data de fechamento de um mês é `closing_day`, limitada ao último dia do mês.
  - A compra na data `d` pertence à fatura cuja data de fechamento é a primeira **estritamente posterior** a `d` (compra no dia do fechamento cai na fatura seguinte).
  - O vencimento é a primeira data com `due_day` (limitado ao fim do mês) depois do fechamento.
  - O backend calcula e grava `invoice_closing_on`. A regra varia entre bancos; se necessário, vira configuração do cartão no futuro.
- F5. Faturas são calculadas, não armazenadas. Valor = Σ despesas do cartão com aquele `invoice_closing_on`; pago = Σ `card_payment` daquela fatura. Status: `open` (antes do fechamento), `closed` (fechada e pago < valor), `paid` (pago ≥ valor), `overdue` (vencida e pago < valor). Pagamento parcial é permitido.
- F6. Limite disponível = `limit_cents` − (Σ despesas no cartão − Σ pagamentos do cartão).
- F7. Categorias padrão são criadas para cada usuário novo e podem ser editadas, arquivadas ou complementadas pela web e pelo app. Despesa: Alimentação, Moradia, Transporte, Saúde, Educação, Lazer, Compras, Assinaturas, Outros. Receita: Salário, Freelance, Rendimentos, Outros.
- F8. Categoria, conta ou cartão com transações não podem ser excluídos, só arquivados (`finance.category_in_use`, `finance.account_in_use`, `finance.card_in_use`). Itens arquivados somem dos seletores, mas continuam nos relatórios.
- F9. Moeda única por usuário (preferência `currency`), por enquanto.
- F10. Compras parceladas (fim da Fase 2): uma compra gera N transações com `installment_group_id`, `installment_number` e `installment_count`, uma por fatura consecutiva.

## Livros (`reading`)

**Book**: `title`, `author`, `total_pages` (> 0), `current_page` (0 a `total_pages`), `status` (`want_to_read` | `reading` | `read`), `owned` (bool: "tenho"), `started_on?`, `finished_on?`, `cover_path?`.

**ReadingProgress**: `book_id`, `page`, `recorded_at`.

**BookNote**: `book_id`, `content` (texto com markdown simples), `page?`.

Regras:
- R1. Status de leitura e posse são independentes: dá para ter um livro que se quer ler e querer ler um livro que não se tem.
- R2. Atualizar o progresso grava uma `ReadingProgress` e atualiza `current_page`.
- R3. Se o status é `want_to_read` e a página passa de 0, o status vira `reading` e `started_on` recebe hoje (se vazio).
- R4. Se a página chega a `total_pages`, o status vira `read` e `finished_on` recebe hoje (se vazio). O usuário pode corrigir editando o livro.
- R5. `progress_percent` = `current_page ÷ total_pages × 100`, calculado pelo backend.
- R6. Capa: JPEG, PNG ou WebP até 5 MB, redimensionada no servidor para no máximo 800 px no maior lado e servida por endpoint autenticado.
