# Arquitetura

## Visão geral

```
                    ┌──────────────────── servidor ─────────────────────┐
 Navegador ───┐     │  web (nginx)                                      │
              ├────►│   ├─ /        → SPA Vue (arquivos estáticos)      │
 App Android ─┘     │   └─ /api/*   → api (FastAPI) ──► db (PostgreSQL) │
                    │                     └──────────► volume uploads   │
                    └───────────────────────────────────────────────────┘
```

O Prumo publica **uma única porta**. O nginx do container `web` serve a SPA e encaminha `/api` para a API, então web e API compartilham a mesma origem (sem CORS, cookies simples). TLS fica a cargo do proxy reverso de quem hospeda.

A web e o Android são clientes equivalentes da mesma API. Nenhuma regra de negócio vive no cliente: se a web mostra "próxima troca de óleo em 580 km", esse número veio pronto da API, e o Android vai mostrar exatamente o mesmo.

## Repositórios

- `prumo` (este): API, web e documentação.
- `prumo-android`: app nativo. Consome o contrato publicado em `openapi/openapi.json`.

## Backend

### Camadas

```
router.py   →   service.py   →   models.py
 (HTTP)        (regras)         (SQLAlchemy)
        ↘  schemas.py (Pydantic: entrada e saída)
```

- **router.py**: recebe a requisição, resolve dependências (sessão, usuário atual), chama o serviço e define status e `response_model`. Não contém regra de negócio.
- **service.py**: regras de negócio, cálculos e transações. Recebe a `Session` e o usuário atual; lança erros de domínio (`DomainError` e subclasses), nunca `HTTPException`.
- **models.py**: modelos SQLAlchemy 2 (`Mapped[...]`).
- **schemas.py**: `XCreate`, `XUpdate` (todos os campos opcionais, PATCH) e `XRead`.

Não há camada de repositório. As consultas ficam no serviço; quando um serviço crescer demais, extraia `queries.py` no mesmo módulo.

A API é síncrona (SQLAlchemy síncrono com psycopg 3; o FastAPI executa rotas síncronas num pool de threads). Ver `docs/decisoes.md`, D05.

### Estrutura

```
backend/
├── pyproject.toml
├── alembic.ini
├── migrations/
├── src/prumo/
│   ├── main.py              # bootstrap() e create_app(): handlers, routers do sistema e dos módulos
│   ├── cli.py               # `prumo users create`, `prumo users set-password`, `prumo openapi`
│   ├── openapi.py           # exportação do contrato
│   ├── core/                # infraestrutura, sem regra de negócio
│   │   ├── config.py        # Settings (pydantic-settings, prefixo PRUMO_)
│   │   ├── clock.py         # utcnow(): o "agora" do backend
│   │   ├── db.py            # engine, Session, Base e mixins (IdMixin, TimestampMixin, UserOwnedMixin)
│   │   ├── deps.py          # SessionDep (CurrentUser fica em system/auth/deps.py; D21)
│   │   ├── errors.py        # DomainError, NotFoundError, ConflictError e handlers
│   │   ├── pagination.py    # PageParams e Page[T]
│   │   ├── security.py      # hash de senha (argon2), geração e hash de tokens
│   │   ├── events.py        # barramento de eventos em processo
│   │   └── modules.py       # PrumoModule, ModuleSummary e o registro de módulos
│   ├── system/              # plataforma: auth/ (sessões, CurrentUser), users/, preferences/, modules/, dashboard/, health.py
│   └── modules/
│       ├── __init__.py      # INSTALLED_MODULES
│       ├── finance/         # Finanças
│       ├── garage/          # Veículos
│       └── reading/         # Livros
└── tests/                   # espelha a estrutura de src/prumo
```

### Módulos

O id do módulo é estável, em inglês, e não é o nome exibido (que vem do i18n).

| id | Nome exibido | Prefixo da API | Prefixo das tabelas |
|---|---|---|---|
| `finance` | Finanças | `/api/v1/finance` | `finance_` |
| `garage` | Veículos | `/api/v1/garage` | `garage_` |
| `reading` | Livros | `/api/v1/reading` | `reading_` |

A ordem acima é a de `INSTALLED_MODULES` e, por isso, a ordem padrão da navegação e do Início para usuários novos (cada usuário pode reordenar). A ordem das fases do ROADMAP é outra coisa.

Estrutura de um módulo:

```
modules/garage/
├── __init__.py   # define `module = PrumoModule(...)`
├── models.py
├── schemas.py
├── service.py
├── router.py
├── summary.py    # resumo exibido no Início
├── events.py     # eventos que o módulo publica (contrato público), se houver
└── defaults.py   # dados iniciais criados para cada usuário, se houver
```

Contrato:

```python
# core/modules.py
@dataclass(frozen=True)
class PrumoModule:
    id: str                                    # "garage": rotas, tabelas, preferências
    version: str
    router: APIRouter                          # montado em /api/v1/{id}, tag {id}
    summary: SummaryProvider | None = None     # (session, user) -> subclasse de ModuleSummary
    on_user_created: UserHook | None = None    # ex.: criar categorias padrão
    event_handlers: Mapping[type[Event], Handler] = field(default_factory=dict)
```

O registro é uma lista explícita, sem descoberta automática:

```python
# modules/__init__.py
INSTALLED_MODULES: list[PrumoModule] = [finance.module, garage.module, reading.module]
```

O schema do resumo é lido da anotação de retorno de `summary`, que deve ser uma subclasse de `ModuleSummary` com `module: Literal["<id>"]` (validado ao criar o módulo). O id segue `^[a-z][a-z0-9_]{1,31}$`.

A partir dessa lista, `prumo.main.bootstrap()` preenche o registro (`core.modules.registry`) e o barramento (`core.events.bus`), injetando nele a checagem de módulo ativo. Em seguida, `create_app()` monta os routers; o `env.py` do Alembic importa os modelos; a criação de usuário (API ou CLI) executa os `on_user_created`; o dashboard agrega os `summary` numa união discriminada; o barramento registra os `event_handlers`.

### Isolamento

- Um módulo importa de `prumo.core` e `prumo.system` (por exemplo, `SessionDep` de `prumo.core.deps` e `CurrentUser` de `prumo.system.auth.deps`).
- Um módulo não importa outro módulo, com uma exceção: o `events.py` público de outro módulo, para assinar eventos.
- `core` não importa `system` nem módulos; `system` não importa módulos (só a lista `INSTALLED_MODULES`, via `main.py`).
- `core`, `system` e os módulos não importam `prumo.main`, `prumo.cli` nem `prumo.openapi`.
- O `import-linter` verifica essas regras no `make lint` (contratos em `backend/pyproject.toml`).

### Eventos entre módulos

Integrações entre módulos (por exemplo, um abastecimento gerar uma despesa em Finanças) usam o barramento de `core/events.py`:

- Eventos são dataclasses imutáveis definidas no `events.py` do módulo que publica.
- A publicação é síncrona e acontece dentro da mesma transação: se um handler falhar, a operação inteira é desfeita.
- Handlers devem tolerar o módulo de destino estar desativado para o usuário (preferência): nesse caso não fazem nada.

Na Fase 0 o barramento existe e é testado com um módulo falso. A primeira integração real está em "Ideias" no ROADMAP.

### Dashboard e módulos ativos

- Todo módulo instalado existe para todos os usuários. A preferência `enabled_modules` (lista ordenada) controla navegação e Início. A API de um módulo desativado continua funcionando: é preferência, não permissão. Um módulo instalado depois aparece ativo, no fim da ordem, para quem já existia (D20).
- `GET /api/v1/dashboard` devolve o resumo de cada módulo ativo, na ordem escolhida pelo usuário. Cada resumo é um schema tipado com o campo `module` como discriminador, para que clientes gerados (TS e Kotlin) tenham tipos precisos.

## Frontend

SPA Vue 3 que espelha o sistema de módulos do backend. Detalhes em `docs/frontend.md`.

## Implantação

`docker-compose.yml` com três serviços:

| Serviço | Papel |
|---|---|
| `db` | PostgreSQL, volume `db_data` |
| `api` | Uvicorn (`--proxy-headers`); no início do container executa `alembic upgrade head`; volume `uploads` |
| `web` | nginx com o build da SPA; encaminha `/api` para `api`; única porta publicada (`PRUMO_PORT`) |

Para desenvolvimento, só o `db` roda em Docker; API e Vite rodam localmente (`make dev`), com o Vite encaminhando `/api` para a API.

## Segurança

- Senhas com argon2.
- Tokens de sessão: 32 bytes aleatórios; o banco guarda apenas o hash SHA-256. Sessões têm expiração e podem ser revogadas individualmente.
- Web: cookie `prumo_session` com `HttpOnly`, `SameSite=Lax` e `Secure` (configurável para desenvolvimento). Requisições que alteram dados com autenticação por cookie exigem o header `X-Prumo-Client: web` (defesa contra CSRF).
- App: `Authorization: Bearer <token>`.
- Limite de tentativas de login por usuário e IP: 5 falhas em 15 minutos bloqueiam por 15 minutos, guardado no banco (D24).
- `last_used_at` da sessão é atualizado no máximo uma vez por minuto.
- Sem cadastro público: usuários são criados pela CLI.
- CORS desativado por padrão (mesma origem); origens adicionais via `PRUMO_CORS_ORIGINS`.
- Uploads validados por tipo e tamanho e servidos apenas por endpoints autenticados.
