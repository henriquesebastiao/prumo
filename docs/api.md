# API

A API é o produto. A web e o app Android são clientes dela, e o contrato publicado em `openapi/openapi.json` é a fonte de verdade para ambos.

## Base e versionamento

- Base: `/api/v1`. Exceção: `GET /api/health` (sem versão, sem autenticação).
- Documentação interativa em `/api/docs` e esquema em `/api/openapi.json`.
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
- `client: "web"`: responde `200` com `{ "user": { … } }` e define o cookie `prumo_session`. Em requisições que alteram dados (`POST`, `PATCH`, `PUT`, `DELETE`), a web envia `X-Prumo-Client: web`.

| Rota | Descrição |
|---|---|
| `POST /auth/login` | Cria sessão (web ou app) |
| `POST /auth/logout` | Revoga a sessão atual |
| `GET /auth/sessions` | Lista sessões ativas do usuário (dispositivo, cliente, último uso) |
| `DELETE /auth/sessions/{id}` | Revoga uma sessão |
| `GET /me` | Usuário atual |
| `PATCH /me` | Atualiza nome de exibição |
| `PUT /me/password` | Troca a senha (exige a atual; revoga as outras sessões) |
| `GET /me/preferences`, `PATCH /me/preferences` | Tema, idioma, fuso, moeda, módulos ativos e ordem |

Validade padrão: 30 dias para web, 180 dias para app (configurável). Login com falhas repetidas responde `429`.

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
| 401 | Não autenticado ou sessão expirada (`auth.required`, `auth.session_expired`) |
| 404 | Recurso inexistente **ou de outro usuário** (`not_found`) |
| 409 | Conflito de unicidade (`finance.category_exists`) |
| 422 | Validação de entrada ou violação de regra de negócio |
| 429 | Limite de tentativas (`auth.rate_limited`) |

## Rotas

Todas abaixo de `/api/v1`. Resumo; o detalhe está no OpenAPI.

### Sistema
| Rota | Descrição |
|---|---|
| `GET /modules` | Módulos instalados, com estado ativo e ordem para o usuário |
| `GET /dashboard` | Resumos dos módulos ativos (Início) |

### Veículos (`/garage`)
| Rota | Descrição |
|---|---|
| `GET, POST /garage/vehicles` | Lista (com status de óleo de cada um) e cadastro |
| `GET, PATCH, DELETE /garage/vehicles/{id}` | Detalhe com informações rápidas (`oil_change`, `stats`), edição, exclusão |
| `POST /garage/vehicles/{id}/archive`, `/unarchive` | Arquivamento |
| `GET, POST /garage/vehicles/{id}/odometer` | Histórico de km e nova leitura manual |
| `DELETE /garage/vehicles/{id}/odometer/{reading_id}` | Remove leitura manual |
| `GET, POST /garage/vehicles/{id}/maintenances` | Lista (filtro `kind=oil_change`) e cadastro com itens |
| `GET, PATCH, DELETE /garage/vehicles/{id}/maintenances/{maintenance_id}` | |
| `GET /garage/vehicles/{id}/oil-change-suggestion?km=…&on=…` | Próxima troca sugerida para um km e data informados (usado no formulário) |
| `GET, POST /garage/vehicles/{id}/fuelings` | Lista e cadastro |
| `GET, PATCH, DELETE /garage/vehicles/{id}/fuelings/{fueling_id}` | |
| `GET, POST /garage/workshops` | Lista com busca (`q`) e cadastro |
| `PATCH, DELETE /garage/workshops/{id}` | |

Exemplo do bloco de informações rápidas no detalhe do veículo:

```json
"oil_change": {
  "status": "due_soon",
  "primary": "km",
  "next_km": 19000, "remaining_km": 580,
  "next_on": "2026-12-10", "remaining_days": 38
},
"stats": {
  "last_fueling": { "fueled_at": "2026-10-30T12:10:00Z", "volume_ml": 9800, "total_cents": 6260 },
  "last_consumption_km_l": 39.1,
  "avg_consumption_km_l": 38.4,
  "month_spent_cents": 31250
}
```

### Finanças (`/finance`)
| Rota | Descrição |
|---|---|
| `GET /finance/overview?month=2026-11` | Saldo total, saldos por conta, receitas × despesas, despesas por categoria, faturas em aberto |
| `GET, POST /finance/accounts` | Lista (com saldo atual) e cadastro |
| `GET, PATCH /finance/accounts/{id}` | Detalhe e edição |
| `POST /finance/accounts/{id}/archive`, `/unarchive` | |
| `GET, POST /finance/categories` | Lista (filtro `kind`) e cadastro |
| `PATCH, DELETE /finance/categories/{id}` | Exclusão só sem uso; caso contrário, arquivar |
| `GET, POST /finance/transactions` | Lista com filtros (`from`, `to`, `kind`, `account_id`, `credit_card_id`, `category_id`, `q`) e cadastro |
| `GET, PATCH, DELETE /finance/transactions/{id}` | |
| `GET, POST /finance/credit-cards` | Lista (com limite disponível e fatura atual) e cadastro |
| `GET, PATCH /finance/credit-cards/{id}` | |
| `GET /finance/credit-cards/{id}/invoices` | Faturas (abertas, fechadas, pagas) |
| `GET /finance/credit-cards/{id}/invoices/{closing_on}` | Fatura com lançamentos |
| `POST /finance/credit-cards/{id}/invoices/{closing_on}/payments` | Registra pagamento (total ou parcial) |

### Livros (`/reading`)
| Rota | Descrição |
|---|---|
| `GET, POST /reading/books` | Lista (filtros `status`, `owned`, `q`) e cadastro |
| `GET, PATCH, DELETE /reading/books/{id}` | Detalhe (com `progress_percent`), edição, exclusão |
| `GET, POST /reading/books/{id}/progress` | Histórico e nova página atual |
| `GET, POST /reading/books/{id}/notes` | Anotações |
| `PATCH, DELETE /reading/books/{id}/notes/{note_id}` | |
| `GET, PUT, DELETE /reading/books/{id}/cover` | Capa (upload `multipart/form-data`) |

## OpenAPI e clientes gerados

- `operation_id` estável no formato `{tag}_{nome_da_funcao}` (ex.: `garage_list_vehicles`), configurado via `generate_unique_id_function`. Renomear uma função de rota muda o contrato.
- `make openapi` grava `openapi/openapi.json` e regenera `frontend/src/lib/api/schema.d.ts` (openapi-typescript). Um teste falha se o snapshot estiver desatualizado.
- O app Android gera ou escreve seus modelos a partir do mesmo arquivo (decisão do repositório `prumo-android`).

## Preparação para o Android (Fase 5)

- Criação idempotente: `POST` aceita `id` gerado pelo cliente, permitindo repetir uma requisição após falha de rede sem duplicar registros.
- Sincronização incremental: listas aceitam `updated_since`, e exclusões ficam registradas para que o app saiba o que remover.
