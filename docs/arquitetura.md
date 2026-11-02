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
│   ├── main.py              # create_app(): middlewares, handlers, routers do sistema e dos módulos
│   ├── cli.py               # `prumo users create`, `prumo users set-password`
│   ├── core/                # infraestrutura, sem regra de negócio
│   │   ├── config.py        # Settings (pydantic-settings, prefixo PRUMO_)
│   │   ├── db.py            # engine, Session, Base e mixins (IdMixin, TimestampMixin, UserOwnedMixin)
│   │   ├── deps.py          # dependências: SessionDep, CurrentUser
│   │   ├── errors.py        # DomainError, NotFoundError, ConflictError e handlers
│   │   ├── pagination.py    # PageParams e Page[T]
│   │   ├── security.py      # hash de senha (argon2), geração e hash de tokens
│   │   ├── events.py        # barramento de eventos em processo
│   │   └── modules.py       # PrumoModule
│   ├── system/              # recursos da plataforma: auth, users, sessions, preferences, modules, dashboard
│   └── modules/
│       ├── __init__.py      # INSTALLED_MODULES
│       ├── garage/          # Veículos
│       ├── finance/         # Finanças
│       └── reading/         # Livros
└── tests/                   # espelha a estrutura de src/prumo
```

### Módulos

O id do módulo é estável, em inglês, e não é o nome exibido (que vem do i18n).

| id | Nome exibido | Prefixo da API | Prefixo das tabelas |
|---|---|---|---|
| `garage` | Veículos | `/api/v1/garage` | `garage_` |
| `finance` | Finanças | `/api/v1/finance` | `finance_` |
| `reading` | Livros | `/api/v1/reading` | `reading_` |

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
    summary: SummaryProvider | None = None     # (session, user) -> schema do resumo
    on_user_created: UserHook | None = None    # ex.: criar categorias padrão
    event_handlers: Mapping[type[Event], Handler] = field(default_factory=dict)
```

O registro é uma lista explícita, sem descoberta automática:

```python
# modules/__init__.py
INSTALLED_MODULES: list[PrumoModule] = [garage.module, finance.module, reading.module]
```

A partir dessa lista: `create_app()` monta os routers; o `env.py` do Alembic importa os modelos; a criação de usuário executa os `on_user_created`; o dashboard agrega os `summary`; o barramento registra os `event_handlers`.

### Isolamento

- Um módulo importa de `prumo.core` e `prumo.system`.
- Um módulo não importa outro módulo, com uma exceção: o `events.py` público de outro módulo, para assinar eventos.
- `core` não importa `system` nem módulos; `system` não importa módulos (só a lista `INSTALLED_MODULES`, via `main.py`).
- O `import-linter` verifica essas regras no `make lint`.

### Eventos entre módulos

Integrações entre módulos (por exemplo, um abastecimento gerar uma despesa em Finanças) usam o barramento de `core/events.py`:

- Eventos são dataclasses imutáveis definidas no `events.py` do módulo que publica.
- A publicação é síncrona e acontece dentro da mesma transação: se um handler falhar, a operação inteira é desfeita.
- Handlers devem tolerar o módulo de destino estar desativado para o usuário (preferência): nesse caso não fazem nada.

Na Fase 0 o barramento existe e é testado com um módulo falso. A primeira integração real está em "Ideias" no ROADMAP.

### Dashboard e módulos ativos

- Todo módulo instalado existe para todos os usuários. A preferência `enabled_modules` (lista ordenada) controla navegação e Início. A API de um módulo desativado continua funcionando: é preferência, não permissão.
- `GET /api/v1/dashboard` devolve o resumo de cada módulo ativo, na ordem escolhida pelo usuário. Cada resumo é um schema tipado com o campo `module` como discriminador, para que clientes gerados (TS e Kotlin) tenham tipos precisos.

## Frontend

SPA Vue 3 que espelha o sistema de módulos do backend. Detalhes em `docs/frontend.md`.

## Implantação

`docker-compose.yml` com três serviços:

| Serviço | Papel |
|---|---|
| `db` | PostgreSQL, volume `db_data` |
| `api` | Uvicorn; no início do container executa `alembic upgrade head`; volume `uploads` |
| `web` | nginx com o build da SPA; encaminha `/api` para `api`; única porta publicada (`PRUMO_PORT`) |

Para desenvolvimento, só o `db` roda em Docker; API e Vite rodam localmente (`make dev`), com o Vite encaminhando `/api` para a API.

## Segurança

- Senhas com argon2.
- Tokens de sessão: 32 bytes aleatórios; o banco guarda apenas o hash SHA-256. Sessões têm expiração e podem ser revogadas individualmente.
- Web: cookie `prumo_session` com `HttpOnly`, `SameSite=Lax` e `Secure` (configurável para desenvolvimento). Requisições que alteram dados com autenticação por cookie exigem o header `X-Prumo-Client: web` (defesa contra CSRF).
- App: `Authorization: Bearer <token>`.
- Limite de tentativas de login por usuário e IP (ex.: 5 falhas em 15 minutos bloqueiam por 15 minutos).
- Sem cadastro público: usuários são criados pela CLI.
- CORS desativado por padrão (mesma origem); origens adicionais via `PRUMO_CORS_ORIGINS`.
- Uploads validados por tipo e tamanho e servidos apenas por endpoints autenticados.
