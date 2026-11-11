# Domínio e regras de negócio

Este documento é a fonte de verdade para regras de negócio. Em caso de conflito com o design, as regras daqui prevalecem e o design prevalece na apresentação. Conflitos devem ser apontados, não resolvidos em silêncio.

Convenções de todas as entidades: `id` (UUID v7), `created_at`, `updated_at`; entidades de usuário têm `user_id`. Os campos abaixo omitem esses.

## Sistema

**User**: `username` (único), `display_name`, `password_hash`, `is_admin`.

**Session**: `token_hash`, `client` (`web` | `app`), `device_name`, `last_used_at`, `expires_at`, `revoked_at`.

**Preferences** (1:1 com User): `theme` (`system` | `light` | `dark`), `locale` (`pt-BR`), `timezone` (padrão da instância), `currency` (padrão `BRL`), `enabled_modules` (lista ordenada de ids; padrão: todos os instalados). Internamente guarda a ordem e os desativados, para que um módulo instalado depois apareça ativo (D20).

Regras:
- S1. Não há cadastro público. Usuários são criados pela CLI; ao criar, executa-se o `on_user_created` de cada módulo.
- S2. Usuários não compartilham dados entre si.
- S3. "Hoje", "este mês" e "data de um registro" são sempre calculados no fuso da preferência do usuário.
- S4. `username` é único sem diferenciar maiúsculas (guardado em minúsculas): 2 a 32 caracteres entre letras, números, `.`, `_` e `-`. Senha de 8 a 128 caracteres.
- S5. Trocar a senha exige a atual e encerra as outras sessões do usuário.

## Veículos (`garage`)

**Vehicle**: `kind` (`car` | `motorcycle`), `name` (apelido exibido), `brand`, `model`, `year`, `fuel_type?` (combustível habitual), `current_km`, `oil_interval_km?`, `oil_interval_months?`, `notes?`, `archived_at?`. `current_km` e `current_km_at` são derivados das leituras (G2) e guardados para consulta rápida.

**OdometerReading**: `vehicle_id`, `km`, `recorded_at`, `source` (`manual` | `maintenance` | `fueling`), `source_id?`.

**Workshop**: `name` (único por usuário, sem diferenciar maiúsculas), `notes?`.

**Maintenance**: `vehicle_id`, `kind` (`general` | `oil_change`), `performed_at`, `km`, `workshop_id?`, `labor_cost_cents`, `notes?`, `oil_type?`, `next_oil_change_km?`, `next_oil_change_on?` (os três últimos só em `oil_change`).

**MaintenanceItem**: `maintenance_id`, `description`, `quantity` (inteiro ≥ 1, padrão 1), `unit_price_cents`.

**Fueling**: `vehicle_id`, `fueled_at`, `km`, `fuel_type`, `volume_ml`, `total_cents`, `full_tank` (bool), `notes?`.

`fuel_type`: `gasoline` (Gasolina comum), `gasoline_additive` (Gasolina aditivada), `gasoline_premium` (Gasolina premium), `ethanol` (Etanol), `diesel` (Diesel), `cng` (GNV).

Regras:
- G1. Intervalos de troca de óleo são opcionais. Sem nenhum, o veículo não exibe status de óleo (`oil_change` é `null`).
- G2. Odômetro. Todo registro com km gera uma `OdometerReading`: o cadastro do veículo (leitura `manual` no momento do cadastro), a leitura manual (inclusive pelo campo de km da edição do veículo), a manutenção e o abastecimento. `current_km` é o km da leitura mais recente no tempo (empate: a criada por último) e `current_km_at`, o horário dela.
- G3. Consistência cronológica. Uma leitura não pode ser menor que outra leitura anterior no tempo nem maior que outra posterior (km iguais são aceitos); caso contrário, `422 garage.odometer_inconsistent` com a leitura conflitante em `details` (`conflict`: `previous` | `next`, `km`, `recorded_at`). Editar ou excluir um registro atualiza a leitura correspondente e recalcula `current_km`. Só leituras `manual` são excluídas diretamente (as outras saem com o registro de origem), e a última leitura do veículo não pode ser excluída (`422 garage.last_reading`).
- G4. Total da manutenção = `labor_cost_cents` + Σ(`quantity` × `unit_price_cents`). Calculado pelo backend e retornado como `total_cents`, junto com `parts_cents`.
- G5. Troca de óleo é uma manutenção com `kind = oil_change` (tem oficina, peças e mão de obra como qualquer manutenção). O backend sugere `next_oil_change_km = km + oil_interval_km` e `next_oil_change_on = data + oil_interval_months` (dia limitado ao fim do mês; a data da troca é tomada no fuso do usuário). Ao criar, campos de próxima troca ausentes recebem a sugestão; `null` explícito significa "sem previsão". O cliente pode alterar os dois valores.
- G6. Status de óleo, a partir da troca de óleo mais recente:
  - `remaining_km = next_oil_change_km − current_km`; `remaining_days = next_oil_change_on − hoje`.
  - O "intervalo" de cada critério é o vão real da última troca até a próxima prevista (`next_oil_change_km − km da troca`, `next_oil_change_on − data da troca`), que é igual ao intervalo do veículo quando a sugestão não foi alterada.
  - `overdue` se qualquer um for ≤ 0; `due_soon` se `remaining_km` ≤ 10% do intervalo em km ou `remaining_days` ≤ 15; senão `ok`. Com intervalo configurado e nenhuma troca registrada, `unknown`.
  - `primary` indica o critério que vence primeiro, ou seja, o de menor fração restante (`remaining / intervalo`). É o que a interface destaca.
  - `used_km_percent` e `used_days_percent` (0 a 100) indicam quanto de cada intervalo já passou.
- G7. Preço por litro (R$) = (`total_cents` ÷ 100) ÷ (`volume_ml` ÷ 1000), com 3 casas decimais, só para exibição.
- G8. Consumo pelo método do tanque cheio. Entre dois abastecimentos com `full_tank`, consumo = (km do atual − km do cheio anterior) ÷ (litros de todos os abastecimentos depois do cheio anterior até o atual, inclusive). O primeiro tanque cheio não gera consumo. `last_consumption_km_l` é o último ciclo; `avg_consumption_km_l` = Σkm ÷ Σlitros de todos os ciclos; `recent_consumption` são os últimos 5 ciclos (gráfico do detalhe). Valores com 2 casas.
- G9. Gasto do mês do veículo = Σ totais de manutenções + Σ totais de abastecimentos no mês, com as contagens de cada um.
- G10. Oficinas: a manutenção aceita `workshop_id` ou `workshop_name`; um nome inexistente cria a oficina. A oficina retorna `maintenances_count` e `last_maintenance_at`. Oficina com manutenções não pode ser excluída (`422 garage.workshop_in_use`).
- G11. Veículo é arquivado por padrão. Exclusão definitiva apaga todo o histórico e exige confirmação explícita no cliente. Listas e Início mostram só veículos não arquivados, salvo filtro.
- G12. Ritmo de uso: `pace_km_per_day` = Δkm ÷ Δdias entre a leitura mais antiga e a mais recente dos últimos 30 dias (incluindo a última leitura anterior à janela, como ponto de partida). Sem duas leituras ou com menos de 1 dia entre elas, `null`. Com ritmo e `remaining_km` > 0, `estimated_km_on = hoje + ⌈remaining_km ÷ ritmo⌉` (data em que o critério de km deve vencer).
- G13. Km rodados no mês = `current_km` − km da última leitura anterior ao início do mês (no fuso do usuário); sem leitura anterior, conta a partir da primeira leitura do mês.
- G14. O óleo usado em trocas anteriores do veículo é sugerido no formulário (`previous_oil_types`, mais recentes primeiro).
- G15. "Vem aí" (Início): uma troca de óleo prevista por veículo ativo com intervalo, na data do critério principal (`estimated_km_on` quando o principal é km, senão `next_oil_change_on`). "Atividade recente": leituras manuais de km, abastecimentos e manutenções.

## Finanças (`finance`)

**Account**: `name`, `kind` (`checking` | `savings` | `cash` | `investment` | `other`), `initial_balance_cents` (pode ser negativo), `color`, `icon`, `include_in_total` (bool), `archived_at?`.

**Category**: `kind` (`income` | `expense`), `name` (único por usuário e `kind`, sem diferenciar maiúsculas), `color`, `icon`, `archived_at?`.

**CreditCard**: `name`, `limit_cents`, `closing_day` (1–31), `due_day` (1–31), `payment_account_id?`, `color`, `archived_at?`.

**Transaction**: `kind`, `amount_cents`, `occurred_on` (data), `occurred_time?` (hora local, só para exibir e ordenar no dia), `description`, `notes?`, `account_id?`, `destination_account_id?`, `credit_card_id?`, `category_id?`, `invoice_closing_on?`, `installment_group_id?`, `installment_number?`, `installment_count?`.

`color` é uma chave da paleta (`green`, `teal`, `cyan`, `blue`, `indigo`, `violet`, `pink`, `red`, `orange`, `amber`, `gray`); `icon` é o nome de um ícone da interface (`wallet`, `bank`, `utensils`…).

Combinações válidas por `kind`:

| kind | account_id | destination_account_id | credit_card_id | category_id | amount_cents |
|---|---|---|---|---|---|
| `income` | obrigatório | — | — | obrigatório (receita) | > 0 |
| `expense` na conta | obrigatório | — | — | obrigatório (despesa) | > 0 |
| `expense` no cartão | — | — | obrigatório | obrigatório (despesa) | > 0 |
| `transfer` | obrigatório (origem) | obrigatório (≠ origem) | — | — | > 0 |
| `card_payment` | obrigatório | — | obrigatório | — | > 0 |
| `adjustment` | obrigatório | — | — | — | ≠ 0 (com sinal) |

Regras:
- F1. Saldo da conta = inicial + receitas − despesas − transferências enviadas + transferências recebidas − pagamentos de fatura + ajustes, considerando as transações até hoje (fuso do usuário). Calculado, não armazenado.
- F2. Saldo total = soma das contas não arquivadas com `include_in_total`.
- F3. Relatórios usam competência: despesa no cartão conta na data da compra. Pagamento de fatura e ajuste nunca são receita nem despesa e não entram em relatórios por categoria (evita contar duas vezes).
- F4. Fatura de uma compra no cartão:
  - A data de fechamento de um mês é `closing_day`, limitada ao último dia do mês.
  - A compra na data `d` pertence à fatura cuja data de fechamento é a primeira **estritamente posterior** a `d` (compra no dia do fechamento cai na fatura seguinte). O período da fatura vai do fechamento anterior (inclusive) até a véspera do fechamento.
  - O vencimento é a primeira data com `due_day` (limitado ao fim do mês) depois do fechamento.
  - O backend calcula e grava `invoice_closing_on`. A regra varia entre bancos; se necessário, vira configuração do cartão no futuro.
- F5. Faturas são calculadas, não armazenadas. Valor = Σ despesas do cartão com aquele `invoice_closing_on`; pago = Σ `card_payment` daquela fatura. Status: `open` (antes do fechamento), `closed` (fechada e pago < valor), `paid` (pago ≥ valor), `overdue` (vencida e pago < valor). Pagamento parcial é permitido.
- F6. Limite disponível = `limit_cents` − (Σ despesas no cartão − Σ pagamentos do cartão), incluindo parcelas futuras.
- F7. Categorias padrão são criadas para cada usuário novo (e, na migration do módulo, para os usuários que já existiam) e podem ser editadas, arquivadas ou complementadas pela web e pelo app. Despesa: Alimentação, Moradia, Transporte, Combustível, Saúde, Educação, Lazer, Compras, Assinaturas, Outros. Receita: Salário, Freelance, Rendimentos, Outros.
- F8. Categoria, conta ou cartão com transações não podem ser excluídos, só arquivados (`finance.category_in_use`, `finance.account_in_use`, `finance.card_in_use`). Itens arquivados somem dos seletores, mas continuam nos relatórios.
- F9. Moeda única por usuário (preferência `currency`), por enquanto.
- F10. Compras parceladas: uma compra no cartão em N parcelas gera N transações com o mesmo `installment_group_id`, `installment_number` (1…N) e `installment_count`. A parcela k tem a data da compra mais k−1 meses (dia limitado ao fim do mês) e cai na k-ésima fatura a partir da fatura da compra (faturas consecutivas). O valor é dividido igualmente e os centavos que sobram vão para a primeira parcela. Editar uma parcela muda só ela; excluir pode remover só ela ou a compra inteira.
- F11. Ajuste de saldo: informando o saldo real de uma conta, o backend cria uma transação `adjustment` com a diferença para o saldo calculado.
- F12. Visão geral do mês: saldo total e saldos por conta (no último dia do mês, ou hoje no mês atual), receitas, despesas (e a fração das receitas), resultado, receitas × despesas dos 6 meses até o mês, despesas e receitas por categoria, faturas não pagas.
- F16. Descrição obrigatória em receitas e despesas; em transferências, pagamentos de fatura e ajustes pode ficar vazia. O `kind` não muda depois de criada.
- F13. Busca de transações: um texto procura na descrição e nas observações; um número também encontra transações com esse valor ("212,40" e "212.40" → R$ 212,40; "212" → de R$ 212,00 a R$ 212,99; "1.500" → R$ 1.500,00).
- F14. Cada conta informa a data da última movimentação e a quantidade de transações no mês.
- F15. "Vem aí" (Início): fechamento e vencimento das faturas não pagas. "Atividade recente": transações.

## Livros (`reading`)

**Book**: `title`, `author`, `total_pages` (> 0), `current_page` (0 a `total_pages`), `status` (`want_to_read` | `reading` | `read`), `owned` (bool: "tenho"), `started_on?`, `finished_on?`, capa opcional.

**ReadingProgress**: `book_id`, `page`, `previous_page`, `recorded_at`.

**BookNote**: `book_id`, `content` (texto com markdown simples), `page?`, `noted_on` (data, padrão hoje).

Regras:
- R1. Status de leitura e posse são independentes: dá para ter um livro que se quer ler e querer ler um livro que não se tem.
- R2. Atualizar o progresso grava uma `ReadingProgress` (com a página anterior) e atualiza `current_page`. Página igual à atual não grava nada.
- R3. Se o status é `want_to_read` e a página passa de 0, o status vira `reading` e `started_on` recebe hoje (se vazio). "Começar a ler" muda o status para `reading` mesmo na página 0.
- R4. Se a página chega a `total_pages`, o status vira `read` e `finished_on` recebe hoje (se vazio). "Marcar como lido" leva a página ao total. O usuário pode corrigir status e datas editando o livro; `current_page` nunca passa de `total_pages`.
- R5. `progress_percent` = `current_page ÷ total_pages × 100`, arredondado (100 só quando termina), calculado pelo backend.
- R6. Capa: JPEG, PNG ou WebP até 5 MB, validada pelo conteúdo, com a orientação EXIF aplicada, redimensionada no servidor para no máximo 800 px no maior lado, regravada em WebP (sem metadados) e servida por endpoint autenticado. Sem capa, os clientes desenham uma com título e autor.
- R7. Ritmo: páginas por dia = páginas avançadas nos últimos 14 dias (página atual menos a página do último registro anterior à janela, ou 0) ÷ dias da janela (14, ou os dias desde o primeiro registro, se forem menos). Sem avanço, não há ritmo.
- R8. Previsão de término: só para livros `reading` com ritmo; hoje + ⌈páginas restantes ÷ ritmo⌉ dias.
- R9. Páginas por semana (semanas de segunda a domingo, no fuso do usuário): avanço de cada semana, da semana do primeiro registro até a do último, no máximo as 8 últimas.
- R10. Anotações são ordenadas por `noted_on` e, no mesmo dia, pela criação, das mais recentes para as mais antigas. A lista geral de anotações busca no texto.
- R11. "Atividade recente" (Início): registros de progresso (com o avanço em páginas) e anotações. Livros não publicam itens em "Vem aí".

## Estudos (`studies`)

Todo estudo (faculdade, dev, inglês) é registrado aqui; Hábitos não registra estudo e os dois módulos não se integram.

**StudyArea**: `name` (1–60), `color` (chave da paleta, como em Finanças), `archived_at?`.

**Subject**: `area_id`, `name` (1–60), `obsidian_uri?` (≤ 512), `archived_at?`. A matéria herda a cor da área.

**Topic**: `subject_id`, `name` (1–80), único na matéria sem diferenciar maiúsculas. É só uma etiqueta de sessão; o checklist fica no Obsidian.

**StudyPlan**: `valid_from` (data), único por usuário. **PlanBlock**: `plan_id`, `subject_id`, `weekdays` (lista não vazia de 0 = segunda a 6 = domingo), `starts_at?` (hora local), `duration_minutes` (1–720).

**StudySession**: `subject_id`, `topic_id?`, `started_at` (data e hora, guardada em UTC), `duration_minutes` (1–720).

Regras:
- E1. Plano vigente: numa data vale o plano de maior `valid_from` ≤ data. Mudar o plano é criar uma versão (`valid_from` ≥ hoje; padrão sugerido ao cliente: a próxima segunda). Uma versão com `valid_from` < hoje é imutável (`422 studies.plan_locked`); com `valid_from` ≥ hoje pode ser editada e excluída. Duas versões na mesma data: `409 studies.plan_date_taken`.
- E2. Meta de uma matéria numa data = Σ `duration_minutes` dos blocos dela no plano vigente cujo `weekdays` contém o dia da semana da data. `starts_at` só ordena a agenda.
- E3. Feito de uma matéria numa data = Σ `duration_minutes` das sessões dela iniciadas naquela data, no fuso do usuário (S3). Uma sessão que cruza a meia-noite conta no dia em que começou.
- E4. Status por matéria e data: `met` (feito ≥ meta > 0), `partial` (0 < feito < meta), `missed` (meta > 0, feito 0, data passada), `in_progress` (hoje, meta > 0, feito < meta), `extra` (sem meta, feito > 0). Matéria sem meta e sem sessão não aparece no dia.
- E5. Dia cumprido: dia com meta em que todas as matérias estão `met`. Dia sem meta não conta.
- E6. Semana: segunda a domingo no fuso do usuário (como R9). Devolve dias cumpridos sobre dias com meta e minutos feitos sobre planejados, no total e por matéria. Na semana atual, os dias com meta contam só até hoje, inclusive.
- E7. Minutos por semana de uma matéria: as 8 últimas semanas, a atual inclusive (como R9).
- E8. `obsidian_uri` só é aceito com o esquema `obsidian://` (`422 studies.invalid_obsidian_uri`); a API não abre nem verifica o vault.
- E9. Arquivamento: arquivar a área só a esconde da lista (as matérias ficam como estão). Matéria arquivada não aceita sessão nem bloco novos (`422 studies.subject_archived`); os blocos que já tem continuam nos planos, mas a matéria deixa de aparecer no dia e na semana. Área com matérias não pode ser excluída (`422 studies.area_in_use`); excluir uma matéria apaga tópicos, sessões e blocos dela (confirmação no cliente, como G11).
- E10. Tópico nasce implícito: a sessão aceita `topic_id` ou `topic_name`, e um nome inexistente cria o tópico (como G10). Só pode ser excluído sem sessões (`422 studies.topic_in_use`).
- E11. "Atividade recente" (Início): as sessões. Estudos não publica itens em "Vem aí".

## Hábitos (`habits`)

Hábitos a praticar (`build`) e a abandonar (`quit`), D47. O tipo e a medida de um hábito não mudam depois de criados.

**Habit**: `name` (1–60), `kind` (`build` praticar | `quit` abandonar), `color`, `icon` (nome livre), `started_on` (data, padrão hoje), `archived_at?`; só em `build`: `measure` (`check` | `quantity`), `target_value` (> 0) e `unit` (1–12) quando `quantity`.

**HabitFrequency** (só `build`): `habit_id`, `valid_from`, `kind` (`daily` | `weekly` | `weekdays`), `times_per_week` (1–7, em `weekly`), `weekdays` (em `weekdays`); única por hábito e data.

**HabitEntry** (só `build`): `habit_id`, `on` (data; a coluna é `day`), `value` (≥ 0; em `check` sempre 1); única por hábito e data. Desmarcar é excluir.

**HabitPause** (só `build`): `habit_id`, `starts_on`, `ends_on?` (≥ `starts_on`); sem fim, em aberto. Pausas não se sobrepõem.

**Relapse** (só `quit`): `habit_id`, `occurred_at`, `note?` (≤ 500).

Regras:
- H1. Dia cumprido: em `check`, existe marcação; em `quantity`, `value ≥ target_value`. Um dia parcial mostra valor e meta e não cumpre.
- H2. Agendado: `daily` todo dia; `weekdays` os dias marcados; `weekly` a unidade é a semana (segunda a domingo, fuso do usuário), cumprida com `times_per_week` dias cumpridos. Não contam dias em pausa, antes de `started_on` nem futuros. A frequência vigente numa data é a de maior `valid_from` ≤ data; mudar cria uma versão (`valid_from` ≥ hoje; passada é imutável, `422 habits.frequency_locked`; repetida, `409 habits.frequency_date_taken`). A primeira versão nasce com o hábito, em `started_on`, e não pode ser excluída; um `started_on` mais cedo a leva junto. Em `weekly`, a semana em que a frequência começa conta só os dias desde `valid_from` e exige o menor entre `times_per_week` e os dias restantes.
- H3. Marcação só de `started_on` até hoje, no fuso do usuário: futuro `422 habits.future_date`, antes do início `422 habits.before_start`. Marcação, pausa e frequência só em `build` (`422 habits.not_build`); recaída só em `quit` (`422 habits.not_quit`).
- H4. Sequência atual, estrita: unidades agendadas consecutivas e cumpridas, de hoje para trás. Hoje não cumprido e a semana `weekly` em andamento não quebram; se já cumpridos, contam. A pausa não quebra nem conta. `best_streak` é a maior já feita.
- H5. Taxa: cumpridos ÷ agendados nos últimos 30 dias, hoje inclusive quando já cumprido (hoje aberto não pesa, como em H4); em `weekly`, nas últimas 4 semanas completas. Sem nada agendado na janela, `null`. A API dá a porcentagem arredondada (`rate_percent`).
- H6. Semana atual em `weekly`: dias cumpridos sobre `times_per_week`.
- H7. Maus hábitos: `clean_since` = última recaída ou `started_on` às 00:00 no fuso; `clean_days` = dias inteiros até agora; `best_clean_days` = maior intervalo entre início, recaídas e agora; `relapses_30d`. Recaída antes do início (`habits.before_start`) ou no futuro (`habits.future_date`) é recusada.
- H8. Hábito arquivado sai das listas, do Hoje e do Início; o histórico fica.
- H9. Início: cumpridos sobre agendados hoje, até 3 pendentes e os maus hábitos com os dias sem. Nada em "Atividade recente" nem em "Vem aí".

