# API

A API é o produto. A web e o app Android são clientes dela, e o contrato publicado em `openapi/openapi.json` é a fonte de verdade para ambos.

## Base e versionamento

- Base: `/api/v1`. Exceção: `GET /api/health` (sem versão, sem autenticação).
- Documentação interativa em `/api/docs` (Swagger UI servido pela própria instância, sem CDN; D39) e esquema em `/api/openapi.json`.
- A v1 só recebe mudanças aditivas: endpoints novos, campos novos opcionais na entrada, campos novos na saída, valores novos de enum.
- Mudança incompatível significa `/api/v2` convivendo com a v1 por um período de transição.
- Clientes devem ignorar campos desconhecidos e tratar valores de enum desconhecidos sem quebrar.

## Autenticação

Um único endpoint de login atende os dois tipos de cliente:

```http
POST /api/v1/auth/login
Content-Type: application/json

{ "username": "ana", "password": "…", "client": "app", "device_name": "Pixel 8" }
```

- `client: "app"`: responde `200` com `{ "token": "…", "expires_at": "…", "user": { … } }`. O app envia `Authorization: Bearer <token>` nas próximas requisições.
- `client: "web"`: responde `200` com `{ "token": null, "expires_at": "…", "user": { … } }` e define o cookie `prumo_session` (`HttpOnly`, `SameSite=Lax`, caminho `/api`). Em requisições que alteram dados (`POST`, `PATCH`, `PUT`, `DELETE`), a web envia `X-Prumo-Client: web`; sem ele, `403 auth.client_header_required`.
- `remember` (opcional, padrão `true`, só web): `false` cria uma sessão curta (`PRUMO_SESSION_HOURS_WEB_TRANSIENT`, 12 h) com cookie que termina ao fechar o navegador (D19).
- `device_name` é opcional; na web, o servidor deriva um nome do User-Agent ("Firefox · Linux").
- O nome de usuário não diferencia maiúsculas.

| Rota | Descrição |
|---|---|
| `POST /auth/login` | Cria sessão (web ou app) |
| `POST /auth/logout` | Revoga a sessão atual |
| `GET /auth/sessions` | Lista sessões ativas do usuário (dispositivo, cliente, último uso, `current`), em `{ "items": [...] }` |
| `DELETE /auth/sessions/{id}` | Revoga uma sessão |
| `GET /me` | Usuário atual |
| `PATCH /me` | Atualiza nome de exibição |
| `PUT /me/password` | Troca a senha (exige a atual; revoga as outras sessões) |
| `GET /me/export` | Exportação dos dados do usuário (D38): `.zip` com `data.json`, um CSV por tabela (`<módulo>/<tabela>.csv`) e os arquivos enviados; sem senha nem sessões |
| `GET /me/preferences`, `PATCH /me/preferences` | Tema, idioma, fuso, moeda, módulos ativos e ordem |

Validade padrão: 30 dias para web, 180 dias para app (configurável). Login com falhas repetidas responde `429` com `Retry-After` (5 falhas em 15 minutos bloqueiam usuário + IP por 15 minutos; D24). Usuário ou senha errados respondem o mesmo `401 auth.invalid_credentials`.

## Convenções de dados

- JSON em `snake_case`.
- IDs: UUID v7 em string.
- Data-hora: ISO 8601 em UTC (`2026-11-02T18:30:00Z`). Na entrada, aceita qualquer offset.
- Data pura (`2026-11-02`) quando o conceito é um dia: data de transação, início e término de leitura, próxima troca de óleo por data.
- Dinheiro: inteiro em centavos, sufixo `_cents` (`"total_cents": 18990`).
- Volume: inteiro em mililitros, sufixo `_ml`. Distância: km inteiros.
- Valores derivados de exibição (preço por litro, consumo em km/l, percentuais) são números calculados pelo backend com precisão documentada no schema.
- Enums: strings minúsculas em `snake_case` (`"oil_change"`, `"due_soon"`).
- Todo recurso retorna `created_at` e `updated_at`.
- `PATCH` é parcial: campo ausente não muda; `null` limpa um campo anulável.

## Listas

```http
GET /api/v1/finance/transactions?limit=50&offset=0&sort=-occurred_on&account_id=…
```

```json
{ "items": [ … ], "total": 312, "limit": 50, "offset": 0 }
```

- `limit` padrão 50, máximo 200.
- Coleções pequenas, sem paginação (`/modules`, `/auth/sessions`), respondem `{ "items": [ … ] }` (D23).
- `sort` aceita um campo permitido pelo endpoint, com `-` para ordem decrescente.
- Filtros são query params documentados em cada endpoint.

## Erros

Formato único para todos os erros:

```json
{
  "error": {
    "code": "garage.odometer_inconsistent",
    "message": "Reading is lower than a previous reading.",
    "details": { "previous_km": 18420, "previous_at": "2026-10-28T18:30:00Z" }
  }
}
```

Erros de validação incluem os campos:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid request.",
    "fields": [ { "path": "items.0.unit_price_cents", "code": "greater_than", "message": "…" } ]
  }
}
```

- `code` é estável e é o que os clientes usam (a web traduz para pt-BR via i18n). `message` é em inglês, para depuração.
- Códigos de domínio levam o id do módulo como prefixo: `garage.odometer_inconsistent`, `finance.category_in_use`.

| Status | Uso |
|---|---|
| 401 | Não autenticado ou sessão expirada (`auth.required`, `auth.session_expired`, `auth.invalid_credentials`) |
| 403 | Mutação por cookie sem `X-Prumo-Client: web` (`auth.client_header_required`) |
| 404 | Recurso inexistente **ou de outro usuário** (`not_found`) |
| 409 | Conflito de unicidade (`finance.category_exists`) |
| 422 | Validação de entrada ou violação de regra de negócio |
| 429 | Limite de tentativas (`auth.rate_limited`) |

## Rotas

Todas abaixo de `/api/v1`. Resumo; o detalhe está no OpenAPI.

### Sistema
| Rota | Descrição |
|---|---|
| `GET /modules` | Módulos instalados na ordem do usuário: `{ "items": [{ "id", "version", "enabled", "position" }] }` |
| `GET /dashboard` | `{ "modules": [ … ] }`: resumo de cada módulo ativo, na ordem do usuário (Início) |

O dashboard também traz `upcoming` (próximos eventos de todos os módulos ativos, por data, até 10, nos próximos 60 dias, incluindo vencidos) e `activity` (registros recentes, do mais novo, até 10). Os dois itens têm `module`, `kind` (código estável, como `garage.oil_change` ou `garage.fueling`, que o cliente traduz), `subject` (nome do que se trata, como o veículo), `entity_id` e `data` (valores simples do evento, documentados por `kind` na seção do módulo); `upcoming` tem `on` (data) e `activity`, `occurred_at`.

Cada resumo do dashboard é um schema do módulo que herda de `ModuleSummary` e fixa `module: Literal["<id>"]`; no OpenAPI, a lista é uma união discriminada por `module` (`oneOf` + `discriminator`). Sem módulos com resumo, os itens usam o schema base `ModuleSummary`.

As preferências (`/me/preferences`) têm `theme` (`system` | `light` | `dark`), `locale` (`pt-BR`), `timezone` (IANA), `currency` (ISO 4217) e `enabled_modules` (ids, em ordem). No `PATCH`, `enabled_modules` lista os ativos na ordem desejada; os instalados que ficarem de fora são desativados. Nenhum desses campos aceita `null`.

### Veículos (`/garage`)
| Rota | Descrição |
|---|---|
| `GET /garage/overview` | Resumo do mês: combustível (total e quantidade), km rodados (total e por veículo) e próximo vencimento de óleo |
| `GET, POST /garage/vehicles` | Lista paginada (filtro `archived`: `false` padrão, `true`, `all`), já com `oil_change` e `stats`; cadastro (cria a leitura inicial) |
| `GET, PATCH, DELETE /garage/vehicles/{id}` | Detalhe com informações rápidas (`oil_change`, `stats`), edição (`current_km` registra uma leitura manual), exclusão definitiva |
| `POST /garage/vehicles/{id}/archive`, `/unarchive` | Arquivamento |
| `GET, POST /garage/vehicles/{id}/odometer` | Histórico de km (mais recente primeiro) e nova leitura manual (`km`, `recorded_at` opcional) |
| `DELETE /garage/vehicles/{id}/odometer/{reading_id}` | Remove leitura manual |
| `GET, POST /garage/vehicles/{id}/maintenances` | Lista (filtro `kind`) e cadastro com itens |
| `GET, PATCH, DELETE /garage/vehicles/{id}/maintenances/{maintenance_id}` | Detalhe, edição (itens enviados substituem os atuais), exclusão |
| `GET /garage/vehicles/{id}/oil-change-suggestion?km=…&on=…` | Próxima troca sugerida para um km e data, mais `previous_oil_types` (usado no formulário) |
| `GET, POST /garage/vehicles/{id}/fuelings` | Lista e cadastro |
| `GET, PATCH, DELETE /garage/vehicles/{id}/fuelings/{fueling_id}` | |
| `GET /garage/maintenances` | Manutenções de todos os veículos (filtros `vehicle_id`, `kind`, `workshop_id`) |
| `GET /garage/fuelings` | Abastecimentos de todos os veículos (filtros `vehicle_id`, `from`, `to`) |
| `GET, POST /garage/workshops` | Lista com busca (`q`) e estatísticas (`maintenances_count`, `last_maintenance_at`); cadastro |
| `PATCH, DELETE /garage/workshops/{id}` | Edição; exclusão só sem manutenções |

Manutenções e abastecimentos retornam o resumo do veículo (`vehicle: { id, name, kind }`), o que permite listas entre veículos sem consultas extras. Manutenções retornam `items`, `parts_cents`, `total_cents` e `workshop` (`{ id, name }` ou `null`); abastecimentos retornam `price_per_liter` e `consumption_km_l` (do ciclo que fecham, ou `null`).

Exemplo do bloco de informações rápidas no detalhe do veículo:

```json
"oil_change": {
  "status": "due_soon",
  "primary": "km",
  "interval_km": 1000, "interval_months": 3,
  "last": { "maintenance_id": "…", "performed_at": "2026-10-21T13:00:00Z", "km": 17640, "oil_type": "4T 20W-50 semissintético" },
  "next_km": 18640, "remaining_km": 220, "used_km_percent": 78,
  "next_on": "2027-01-21", "remaining_days": 65, "used_days_percent": 29,
  "estimated_km_on": "2026-11-25"
},
"stats": {
  "last_fueling": { "id": "…", "fueled_at": "2026-11-16T21:10:00Z", "volume_ml": 7300, "total_cents": 4636, "price_per_liter": 6.351, "full_tank": true },
  "last_consumption_km_l": 40.1,
  "avg_consumption_km_l": 40.4,
  "recent_consumption": [ { "fueling_id": "…", "fueled_at": "2026-11-16T21:10:00Z", "km_l": 40.1 } ],
  "pace_km_per_day": 29.3,
  "month_km": 463,
  "month_spent_cents": 9070, "month_fuelings_count": 2, "month_maintenances_count": 0
}
```

Itens do Início publicados pelo módulo:

| `kind` | Onde | `subject` / `entity_id` | `data` |
|---|---|---|---|
| `garage.oil_change` | `upcoming` | veículo / veículo | `basis` (`km_pace` ou `date`), `status`, `remaining_km`, `remaining_days`, `pace_km_per_day`, `interval_months` |
| `garage.odometer` | `activity` | veículo / veículo | `km` |
| `garage.fueling` | `activity` | veículo / abastecimento | `vehicle_id`, `km`, `volume_ml`, `total_cents` |
| `garage.maintenance` | `activity` | veículo / manutenção | `vehicle_id`, `maintenance_kind`, `km`, `total_cents`, `items_count`, `workshop` |

Erros do módulo: `garage.odometer_inconsistent` (com `details.conflict`, `km`, `recorded_at`), `garage.last_reading`, `garage.reading_not_manual`, `garage.workshop_in_use`, `garage.workshop_exists`, `garage.oil_fields_require_oil_change`, `garage.fuel_type_required`.

### Finanças (`/finance`)
| Rota | Descrição |
|---|---|
| `GET /finance/overview?month=2026-11` | Visão geral do mês (F12); sem `month`, o mês atual |
| `GET, POST /finance/accounts` | Lista `{items, total_balance_cents}` (cada conta com saldo, última movimentação e transações do mês; filtro `archived`) e cadastro |
| `GET, PATCH, DELETE /finance/accounts/{id}` | Detalhe, edição, exclusão (só sem transações) |
| `POST /finance/accounts/{id}/archive`, `/unarchive` | |
| `POST /finance/accounts/{id}/adjustments` | Ajuste de saldo (F11): `{ "balance_cents": …, "occurred_on": … }` |
| `GET, POST /finance/categories` | Lista (filtros `kind`, `archived`; com quantidade e total no mês `month`) e cadastro |
| `PATCH, DELETE /finance/categories/{id}` | Exclusão só sem uso; caso contrário, arquivar |
| `POST /finance/categories/{id}/archive`, `/unarchive` | |
| `GET, POST /finance/transactions` | Lista paginada com filtros (`from`, `to`, `kind`, `account_id`, `credit_card_id`, `category_id`, `q`) e os totais `income_cents` e `expense_cents` do filtro inteiro; cadastro (com `installments` para compra parcelada no cartão; devolve a primeira parcela) |
| `GET, PATCH, DELETE /finance/transactions/{id}` | `DELETE ?installments=all` remove a compra parcelada inteira |
| `GET, POST /finance/credit-cards` | Lista (com limite disponível e fatura atual) e cadastro |
| `GET, PATCH, DELETE /finance/credit-cards/{id}` | Exclusão só sem transações |
| `POST /finance/credit-cards/{id}/archive`, `/unarchive` | |
| `GET /finance/credit-cards/{id}/invoices` | Faturas (abertas, fechadas, pagas), mais recentes primeiro |
| `GET /finance/credit-cards/{id}/invoices/{closing_on}` | Fatura com lançamentos |
| `POST /finance/credit-cards/{id}/invoices/{closing_on}/payments` | Registra pagamento (total ou parcial) |

Transações retornam `account`, `destination_account`, `credit_card` e `category` resumidos (`{ id, name, … }`), para listas sem consultas extras. Faturas retornam `closing_on`, `due_on`, `starts_on` (primeiro dia do período), `amount_cents`, `paid_cents`, `status`, `transactions_count` e o último pagamento (`last_payment_on`, `last_payment_account`). `kind` não pode ser alterado no `PATCH` de transação; `card_payment` criado por `POST /finance/transactions` exige `invoice_closing_on`.

Itens do Início publicados pelo módulo:

| `kind` | Onde | `subject` / `entity_id` | `data` |
|---|---|---|---|
| `finance.invoice_closing` | `upcoming` | cartão / cartão | `amount_cents`, `available_limit_cents` |
| `finance.invoice_due` | `upcoming` | cartão / cartão | `amount_cents`, `paid_cents`, `status` |
| `finance.transaction` | `activity` | descrição / transação | `transaction_kind`, `amount_cents`, `category`, `account`, `credit_card` |

Erros do módulo: `finance.category_in_use`, `finance.account_in_use` e `finance.card_in_use` (com `details.transactions_count`), `finance.category_exists` (409), `finance.invalid_combination` (com `details.kind`, `details.missing` e `details.unexpected`: os campos que faltam ou sobram para o `kind`), `finance.invalid_amount`, `finance.category_kind_mismatch`, `finance.same_account`, `finance.installments_require_card`, `finance.invalid_invoice` e `finance.balance_unchanged` (ajuste sem diferença). Conta, categoria ou cartão de outro usuário citado no corpo responde 404.

### Livros (`/reading`)
| Rota | Descrição |
|---|---|
| `GET, POST /reading/books` | Lista paginada (filtros `status`, `owned`, `q` em título e autor; `sort`) e cadastro |
| `GET, PATCH, DELETE /reading/books/{id}` | Detalhe (com `weekly_pages`, R9), edição, exclusão (com histórico, anotações e capa) |
| `GET, POST /reading/books/{id}/progress` | Histórico e nova página atual (R2–R4) |
| `GET, POST /reading/books/{id}/notes` | Anotações do livro (`{items}`) |
| `PATCH, DELETE /reading/books/{id}/notes/{note_id}` | |
| `GET /reading/notes` | Todas as anotações, paginadas, com o livro resumido (busca `q`) |
| `GET, PUT, DELETE /reading/books/{id}/cover` | Capa: `PUT` com `multipart/form-data` (campo `file`), `GET` devolve `image/webp` |
| `GET /reading/overview` | Contagens da estante por status |

Livros retornam `progress_percent` (R5), `remaining_pages`, `pace_pages_per_day` (R7), `forecast_finish_on` (R8), `last_progress_at`, `notes_count` e `has_cover`. Anotações retornam `book` resumido (`{ id, title, author }`).

Itens do Início publicados pelo módulo:

| `kind` | Onde | `subject` / `entity_id` | `data` |
|---|---|---|---|
| `reading.progress` | `activity` | título / livro | `page`, `pages` (avanço), `total_pages`, `status` |
| `reading.note` | `activity` | título / livro | `page`, `excerpt` |

Erros do módulo: `reading.page_out_of_range`, `reading.invalid_cover` (tipo ou conteúdo), `reading.cover_too_large` (413), `reading.invalid_dates` (término antes do início).

## OpenAPI e clientes gerados

- `operation_id` estável no formato `{tag}_{nome_da_funcao}` (ex.: `garage_list_vehicles`), configurado via `generate_unique_id_function`. Renomear uma função de rota muda o contrato.
- `make openapi` grava `openapi/openapi.json` (via `prumo openapi`) e regenera `frontend/src/lib/api/schema.d.ts` (openapi-typescript). O `make check` e o CI falham se o snapshot ou os tipos estiverem desatualizados.
- Todos os erros 4xx/5xx documentados usam o schema `ErrorResponse`, inclusive os 422 automáticos de validação.
- O app Android gera ou escreve seus modelos a partir do mesmo arquivo (decisão do repositório `prumo-android`).

## Preparação para o Android (Fase 5)

- Criação idempotente: `POST` aceita `id` gerado pelo cliente, permitindo repetir uma requisição após falha de rede sem duplicar registros.
- Sincronização incremental: listas aceitam `updated_since`, e exclusões ficam registradas para que o app saiba o que remover.
