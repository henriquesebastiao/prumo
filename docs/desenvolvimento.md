# Desenvolvimento

## Requisitos

- Docker com Compose
- [uv](https://docs.astral.sh/uv/) (instala o Python 3.14 do projeto)
- Node.js 26 (LTS) com pnpm 12. O Node 25+ não traz mais o corepack: instale com `npm install --global pnpm`
- make
- Para `make screenshots`, uma vez: `cd frontend && pnpm exec playwright install chromium`

## Primeira execução

```bash
cp .env.example .env
(cd backend && uv sync) && (cd frontend && pnpm install)
make dev          # sobe o PostgreSQL, aplica migrations, inicia API (:8000) e Vite (:5173)
make user         # cria o primeiro usuário (interativo), em outro terminal
```

Acesse `http://localhost:5173`. O Vite encaminha `/api` para a API, então o comportamento de origem única é o mesmo da produção. O `make dev` usa `PRUMO_COOKIE_SECURE=false`. A vitrine de componentes fica em `http://localhost:5173/dev/ui` e a documentação interativa da API em `/api/docs`.

## Comandos

| Comando | O que faz |
|---|---|
| `make dev` | Banco no Docker + API com reload + Vite |
| `make db-up` / `make db-down` | Sobe ou para os bancos de desenvolvimento e de testes |
| `make check` | Tudo o que o CI roda: lint, typecheck, testes, snapshot OpenAPI |
| `make test` | Testes de backend e frontend |
| `make lint` | ruff, import-linter, ESLint, Stylelint |
| `make typecheck` | mypy e vue-tsc |
| `make format` | ruff format/fix, Prettier, ESLint e Stylelint com correção |
| `make screenshots` | Playwright: captura as telas e monta comparativos com `design/v1/` em `frontend/e2e/output/compare/` |
| `make migration m="add fuelings"` | Gera migration com autogenerate |
| `make migrate` | Aplica migrations |
| `make openapi` | Exporta `openapi/openapi.json` e regenera `frontend/src/lib/api/schema.d.ts` |
| `make user` | Cria usuário pela CLI |
| `make backup` | Gera `backups/prumo-AAAAMMDD-HHMM.sql.gz` e, na stack de produção, `…-uploads.tar.gz` com as capas (`COMPOSE_FILE=docker-compose.dev.yml` para o banco de desenvolvimento) |
| `make restore f=<arquivo>` | Restaura um backup (substitui o banco atual e, se houver o `…-uploads.tar.gz` correspondente, os arquivos; pede confirmação) |
| `make changelog` | Gera o `CHANGELOG` a partir das issues, pull requests e tags do GitHub (exige o `github_changelog_generator`) |

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `PRUMO_DATABASE_URL` | `postgresql+psycopg://prumo:prumo@localhost:5432/prumo` | Conexão com o banco (no compose de produção é montada a partir de `POSTGRES_*`) |
| `PRUMO_TEST_DATABASE_URL` | `postgresql+psycopg://prumo:prumo@localhost:5433/prumo_test` | Banco dos testes (recriado a cada execução) |
| `PRUMO_COOKIE_SECURE` | `true` | `false` apenas em desenvolvimento sem HTTPS |
| `PRUMO_SESSION_DAYS_WEB` | `30` | Validade da sessão web |
| `PRUMO_SESSION_DAYS_APP` | `180` | Validade da sessão do app |
| `PRUMO_SESSION_HOURS_WEB_TRANSIENT` | `12` | Validade da sessão web sem "Manter conectado" |
| `PRUMO_LOGIN_MAX_FAILURES`, `PRUMO_LOGIN_WINDOW_MINUTES`, `PRUMO_LOGIN_LOCKOUT_MINUTES` | `5`, `15`, `15` | Limite de tentativas de login |
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
- O schema do banco de testes é recriado a partir das migrations no início de cada execução, então as migrations também são testadas.
- Cada teste roda dentro de uma transação revertida no fim (o `commit()` do código só libera um savepoint), então os testes não dependem de ordem.
- Fixtures principais: `db` (sessão), `user` e `other_user`, `client` (sem autenticação), `auth_client` (bearer de `user`), `other_client` (bearer de `other_user`) e `make_app(modules)` (aplicação com módulos falsos, como os de `tests/fakes/modules.py`).
- Fábricas simples em `tests/factories.py` (funções que criam registros com valores padrão).
- Tempo congelado com `time-machine` em regras que dependem de "hoje" (status de óleo, faturas, progresso).
- Todo endpoint tem no mínimo: caminho feliz, validação, e acesso por `other_user` retornando 404.
- A estrutura de `tests/` espelha a de `src/prumo/`.

## Testes do frontend

- Vitest para `lib/` (formatadores, cliente da API, utilitários), registro de módulos, composables e componentes de `src/ui/`.
- Playwright para screenshots de comparação com o design (`make screenshots`, fora do `make check` porque exige o navegador) e, a partir da Fase 4, E2E dos fluxos principais. As telas de plataforma usam API simulada (`e2e/fixtures.ts`); as de módulo usam uma API real iniciada pelo próprio Playwright (`backend/scripts/e2e_server.py`, porta 8001), que recria o banco `prumo_e2e` no container de testes, semeia os dados das pranchas e roda com o relógio no momento delas (17/11/2026, 14:30). Usuário: `henrique` / `prumo-demo-01`.

Os fluxos principais (login, Finanças, Veículos, Livros, exportação e `/api/docs`) ficam em `frontend/e2e/flows.spec.ts` e rodam contra a mesma API semeada das capturas, com a conta vazia `teste` (senha `prumo-teste-01`), sem tocar nos dados das pranchas: `pnpm exec playwright test e2e/flows.spec.ts` em `frontend/`. O CI roda esses fluxos a cada push. `e2e/responsive.spec.ts` verifica celular e tablet (sem rolagem horizontal) e grava as capturas em `e2e/output/responsive/`.

## Migrations

- Gere com `make migration m="…"` e **revise o arquivo**: autogenerate não detecta tudo (renomeações, dados, constraints específicas).
- Nunca edite uma migration já commitada; crie outra.
- Migrations que transformam ou apagam dados precisam de aprovação e de um caminho de `downgrade` pensado.

## Contrato OpenAPI

- O snapshot em `openapi/openapi.json` é versionado e verificado pelo `make check`.
- Mudou rota, schema ou nome de função de rota? `make openapi` e commit do snapshot e dos tipos junto com a mudança.

## CI

Workflow em `.github/workflows/ci.yml` (sintaxe compatível com Forgejo Actions), com três jobs: backend (lint, mypy, pytest com PostgreSQL em service container, snapshot OpenAPI), frontend (lint, vue-tsc, Vitest, tipos gerados e build) e imagens (build de `deploy/api.Dockerfile` e `deploy/web.Dockerfile`, sem publicar).

## Imagens e versões

O `docker-compose.yml` usa as imagens do GHCR (`PRUMO_VERSION`, padrão `latest`). Para testar as imagens construídas a partir do código, some o override: `docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build`. O workflow `release.yml` publica as imagens quando uma tag de versão sem prefixo (`0.1.0`) é enviada (D37); o passo a passo está em [instalacao.md](instalacao.md#publicar-uma-versão-mantenedores).

## Backup e restauração

`make backup` (`deploy/backup.sh`) executa `pg_dump --clean --if-exists` no container `db` e grava um arquivo compactado em `backups/` (fora do controle de versão); na stack de produção, também empacota o volume `uploads` (capas) num `.tar.gz` com o mesmo nome. `make restore` restaura os dois quando encontra o par. Em produção, agende o mesmo script (por exemplo, com cron) e copie os arquivos para fora do servidor. `make restore f=<arquivo>` (`deploy/restore.sh`) para a API, recria os objetos do banco a partir do backup e religa a API; `PRUMO_RESTORE_CONFIRM=yes` dispensa a confirmação.
