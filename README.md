# Prumo

[![CodSpeed](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://app.codspeed.io/henriquesebastiao/prumo?utm_source=badge)

Modular, self-hosted personal organization: vehicles, finances, books and whatever comes next, running on your own server.

> In Portuguese, *estar no prumo* means to be in order, aligned (a *prumo* is a plumb line). That is what Prumo tries to do for everyday life: one place, under your control, to record and keep track of the things that matter.

**Status:** early development, heading to version 0.1. See the [ROADMAP](ROADMAP.md). The interface is in Brazilian Portuguese for now, and so is the technical documentation in `docs/`.

## Features

**Finanças (finances).** Accounts and balances with adjustments; income, expenses and transfers with search by text or value; categories; credit cards with invoices, available limit, payments and installments; a monthly overview with a six-month chart and spending by category.

**Veículos (vehicles).** Cars and motorcycles with an odometer you can update at any time; maintenances with parts, labor and workshop; oil changes with the next one due by km or by date, estimated from your pace; fuelings with price per liter and consumption.

**Livros (books).** The books you own, are reading or want to read; reading progress with history, pace and a finish forecast; notes per book; covers.

**Início (home).** A card per module, quick actions (press `N` anywhere), what is coming up next and recent activity across modules.

**And more to come.** Each area of life is an independent module. New modules plug in without touching the existing ones, and each person turns on only the modules they use.

## Principles

- **Your data, your server.** Self-hosted, no third-party services (not even a CDN), simple backups and a full export of your data (JSON, CSV and files).
- **API first.** Everything the web app does goes through a documented API (`/api/docs`). The Android app uses the same API.
- **Modular.** Isolated modules with the same contract on the backend and the frontend.
- **Multi-user.** One instance can serve several people, each with their own data.
- **Replaceable design.** Look and feel live in design tokens and an in-house component library, so the interface can evolve without rewriting screens.

## Stack

| Layer | Technology |
|---|---|
| API | Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Database | PostgreSQL |
| Web | Vue 3, TypeScript, Vite, Vue Router, TanStack Query, vue-i18n, Reka UI |
| Android | Kotlin, Jetpack Compose, Material 3 Expressive (`prumo-android` repository, coming soon) |
| Deployment | Docker Compose, nginx, images on GitHub Container Registry |

## Self-hosting

Requirements: Docker with the Compose plugin and, outside `localhost`, a reverse proxy with HTTPS.

```bash
mkdir prumo && cd prumo
base=https://raw.githubusercontent.com/henriquesebastiao/prumo/0.1.0
curl -fsSLO "$base/docker-compose.yml"
curl -fsSL "$base/.env.example" -o .env     # set POSTGRES_PASSWORD, PRUMO_VERSION, PRUMO_PORT
docker compose up -d
docker compose exec api prumo users create --admin
```

Open `http://<your-server>:<PRUMO_PORT>` (through your HTTPS proxy). There is no public sign-up: users are created from the command line. Database migrations run automatically when the API starts.

The full guide, with backups, updates and building the images yourself, is in [docs/instalacao.md](docs/instalacao.md) (in Portuguese).

> **Secure cookie.** With `PRUMO_COOKIE_SECURE=true` (the default), browsers only send the session cookie over HTTPS, so web login does not work over plain `http://` except on `localhost`. Use a TLS reverse proxy or, on a trusted network only, set `PRUMO_COOKIE_SECURE=false`.

## Development

Requirements: Docker, [uv](https://docs.astral.sh/uv/), Node.js 26 with pnpm 12, and make.

```bash
cp .env.example .env
(cd backend && uv sync) && (cd frontend && pnpm install)
make dev        # PostgreSQL in Docker, API with reload and the Vite dev server
make user       # create the first user
make check      # lint, types, tests and the OpenAPI snapshot
```

`make screenshots` captures every screen with Playwright and builds side-by-side comparisons with the design. See [docs/desenvolvimento.md](docs/desenvolvimento.md) for the complete guide.

## Repository layout

```
prumo/
├── backend/     FastAPI app (prumo package), migrations and tests
├── frontend/    Vue 3 SPA
├── design/      Design exports (visual reference only)
├── openapi/     Snapshot of the API contract
├── deploy/      Dockerfiles, nginx configuration and backup scripts
└── docs/        Technical documentation (Portuguese)
```

## Documentation

- [Architecture](docs/arquitetura.md)
- [API](docs/api.md)
- [Domain and business rules](docs/dominio.md)
- [Frontend and design system](docs/frontend.md)
- [Development](docs/desenvolvimento.md)
- [Self-hosting](docs/instalacao.md)
- [Creating a module](docs/novo-modulo.md)
- [Technical decisions](docs/decisoes.md)

## Contributing

Issues and suggestions are welcome. Before opening a pull request, read the architecture and development guides. Ideas for new modules can start as an issue.

## License

[GNU Affero General Public License v3.0 or later](LICENSE) (`AGPL-3.0-or-later`). If you modify Prumo and offer it to other people over a network, you must make your modified source code available to them.

---

Made by [Henrique Sebastião](https://henriquesebastiao.com).
