# Desenvolvimento

## Requisitos

- Docker com Compose
- [uv](https://docs.astral.sh/uv/) (instala o Python 3.14 do projeto)
- Node.js LTS com pnpm (via `corepack enable`)
- make

## Primeira execução

```bash
cp .env.example .env
make dev          # sobe o PostgreSQL, aplica migrations, inicia API (:8000) e Vite (:5173)
make user         # cria o primeiro usuário (interativo)
```

Acesse `http://localhost:5173`. O Vite encaminha `/api` para a API, então o comportamento de origem única é o mesmo da produção.

## Comandos

| Comando | O que faz |
|---|---|
| `make dev` | Banco no Docker + API com reload + Vite |
| `make check` | Tudo o que o CI roda: lint, typecheck, testes, snapshot OpenAPI |
| `make test` | Testes de backend e frontend |
| `make lint` | ruff, import-linter, ESLint, Stylelint |
| `make typecheck` | mypy e vue-tsc |
| `make migration m="add fuelings"` | Gera migration com autogenerate |
| `make migrate` | Aplica migrations |
| `make openapi` | Exporta `openapi/openapi.json` e regenera `frontend/src/lib/api/schema.d.ts` |
| `make user` | Cria usuário pela CLI |
| `make backup` | Gera `backups/prumo-AAAAMMDD-HHMM.sql.gz` |
| `make restore f=<arquivo>` | Restaura um backup (substitui o banco atual) |

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `PRUMO_DATABASE_URL` | `postgresql+psycopg://prumo:prumo@localhost:5432/prumo` | Conexão com o banco |
| `PRUMO_COOKIE_SECURE` | `true` | `false` apenas em desenvolvimento sem HTTPS |
| `PRUMO_SESSION_DAYS_WEB` | `30` | Validade da sessão web |
| `PRUMO_SESSION_DAYS_APP` | `180` | Validade da sessão do app |
| `PRUMO_DEFAULT_TIMEZONE` | `America/Sao_Paulo` | Fuso padrão de novos usuários |
| `PRUMO_DEFAULT_LOCALE` | `pt-BR` | Idioma padrão |
| `PRUMO_DEFAULT_CURRENCY` | `BRL` | Moeda padrão |
| `PRUMO_UPLOADS_DIR` | `/data/uploads` | Arquivos enviados (capas) |
| `PRUMO_CORS_ORIGINS` | vazio | Origens extras permitidas, separadas por vírgula |
| `PRUMO_PORT` | `8080` | Porta publicada pelo container `web` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | — | Usadas pelo compose |

## Fluxo de trabalho

1. Pegue o próximo item do `ROADMAP.md`.
2. Se tocar em regra de negócio ou na API, atualize primeiro `docs/dominio.md` ou `docs/api.md`.
3. Implemente backend (modelo → migration → serviço → testes → router → testes de API), depois `make openapi`, depois frontend.
4. `make check` verde, item marcado no ROADMAP, commit no padrão Conventional Commits.

## Testes do backend

- PostgreSQL real: o compose de desenvolvimento sobe também um banco de testes; no CI, um service container.
- Cada teste roda dentro de uma transação revertida no fim, então os testes não dependem de ordem.
- Fixtures principais: `db` (sessão), `user` e `other_user`, `client` (sem autenticação), `auth_client` (autenticado como `user`).
- Fábricas simples em `tests/factories.py` (funções que criam registros com valores padrão).
- Tempo congelado com `time-machine` em regras que dependem de "hoje" (status de óleo, faturas, progresso).
- Todo endpoint tem no mínimo: caminho feliz, validação, e acesso por `other_user` retornando 404.
- A estrutura de `tests/` espelha a de `src/prumo/`.

## Testes do frontend

- Vitest para `lib/` (formatadores, utilitários), composables e componentes de `src/ui/`.
- Playwright para screenshots de comparação com o design e, a partir da Fase 4, E2E dos fluxos principais.

## Migrations

- Gere com `make migration m="…"` e **revise o arquivo**: autogenerate não detecta tudo (renomeações, dados, constraints específicas).
- Nunca edite uma migration já commitada; crie outra.
- Migrations que transformam ou apagam dados precisam de aprovação e de um caminho de `downgrade` pensado.

## Contrato OpenAPI

- O snapshot em `openapi/openapi.json` é versionado e verificado pelo `make check`.
- Mudou rota, schema ou nome de função de rota? `make openapi` e commit do snapshot e dos tipos junto com a mudança.

## CI

Workflow em `.github/workflows/ci.yml` (sintaxe compatível com Forgejo Actions): lint, typecheck, testes de backend com PostgreSQL, testes de frontend, verificação do snapshot OpenAPI e build da imagem.

## Backup e restauração

`make backup` executa `pg_dump` no container `db` e grava um arquivo compactado em `backups/` (fora do controle de versão). Em produção, agende o mesmo script (por exemplo, com cron) e copie os arquivos para fora do servidor. `make restore f=<arquivo>` recria o banco a partir de um backup.
