# Prumo

[![CodSpeed](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://app.codspeed.io/henriquesebastiao/prumo?utm_source=badge)

Organização pessoal em módulos, open source e self-hosted: finanças, veículos, livros, estudos e hábitos, rodando no seu próprio servidor.

> *Estar no prumo* é estar em ordem, alinhado (o prumo é o fio com um peso na ponta que o pedreiro usa para conferir se a parede está reta). É isso que o Prumo tenta fazer pelo dia a dia: um só lugar, sob o seu controle, para registrar e acompanhar o que importa.

**Situação:** versão 0.4.0, com todos os módulos planejados prontos. O projeto está completo para o uso pretendido; novas funcionalidades podem chegar quando surgirem novas ideias (veja a seção "Ideias" do [ROADMAP](ROADMAP.md)). A interface e a documentação estão em português do Brasil.

Este repositório tem o servidor: a API e a interface web. O app Android nativo fica em [prumo-android](https://github.com/henriquesebastiao/prumo-android) e usa a mesma API.

## Funcionalidades

**Início.** Um card por módulo com o resumo do momento, ações rápidas (tecle `N` em qualquer tela, ou o atalho de cada ação), "Vem aí" com o que está para vencer e "Atividade recente" de todos os módulos.

**Finanças.** Contas e saldos, com ajuste de saldo; receitas, despesas e transferências, com filtros e busca por texto ou valor; categorias com cor e ícone; cartões de crédito com faturas, limite disponível, pagamento e compras parceladas; visão do mês com gráfico de seis meses e gastos e receitas por categoria.

**Veículos.** Carros e motos com odômetro atualizável a qualquer momento; manutenções com peças, mão de obra e oficina (com autocompletar); trocas de óleo com a próxima prevista por km ou por data, estimada pelo seu ritmo de uso; abastecimentos com preço por litro e consumo pelo método do tanque cheio; histórico de consumo e gastos.

**Livros.** Os livros que você tem, está lendo ou quer ler; progresso de leitura com histórico, ritmo, páginas por semana e previsão de término; anotações por livro; capas enviadas pela web ou pelo app.

**Estudos.** Áreas e matérias (com link para a nota no Obsidian), tópicos criados pelo nome, um plano semanal versionado e sessões de estudo. Mostra o dia (meta e feito por matéria), a semana (dias cumpridos e minutos) e o histórico das últimas semanas.

**Hábitos.** Hábitos a praticar (marcar ou medir uma quantidade) e a abandonar (dias sem e recaídas). Frequências diárias, em dias da semana, a cada N semanas, em dias do mês, no "primeiro domingo" e afins, ou X vezes por semana, quinzena ou mês; pausas; horário opcional e ordem manual. A tela Hoje agrupa o dia (com horário, sem horário, neste período, feitos), e cada hábito tem sequência, melhor sequência, taxa de cumprimento e calendário do mês.

**Sistema.** Vários usuários na mesma instância, cada um com seus dados; preferências de tema, fuso, moeda e módulos ativos (com a ordem da navegação); sessões ativas com revogação; troca de senha; exportação completa dos seus dados (JSON, CSV e capas).

## Princípios

- **Seus dados, seu servidor.** Self-hosted, sem serviços de terceiros (nem CDN), backup simples e exportação completa dos dados.
- **API primeiro.** Tudo o que a web faz passa por uma API documentada (`/api/docs`). O app Android usa a mesma API, e nenhum cliente calcula regra de negócio: saldos, faturas, consumo, progresso e sequências vêm prontos do servidor.
- **Modular.** Cada área da vida é um módulo isolado, com o mesmo contrato no backend e no frontend. Cada pessoa liga só os módulos que usa.
- **Design substituível.** Aparência em tokens e numa biblioteca de componentes própria, para a interface evoluir sem reescrever telas.

## Tecnologias

| Camada | Tecnologia |
|---|---|
| API | Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Banco | PostgreSQL |
| Web | Vue 3, TypeScript, Vite, Vue Router, TanStack Query, vue-i18n, Reka UI |
| Android | Kotlin, Jetpack Compose, Material 3 Expressive ([prumo-android](https://github.com/henriquesebastiao/prumo-android)) |
| Implantação | Docker Compose, nginx, imagens no GitHub Container Registry |

## Instalação (self-host)

Requisitos: um servidor Linux com Docker e o plugin Compose (amd64 ou arm64) e, fora de `localhost`, um proxy reverso com HTTPS.

```bash
mkdir prumo && cd prumo
base=https://raw.githubusercontent.com/henriquesebastiao/prumo/0.4.0
curl -fsSLO "$base/docker-compose.yml"
curl -fsSL "$base/.env.example" -o .env     # ajuste POSTGRES_PASSWORD, PRUMO_VERSION e PRUMO_PORT
docker compose up -d
docker compose exec api prumo users create --admin
```

Acesse `http://<seu-servidor>:<PRUMO_PORT>` (pelo proxy com HTTPS). Não existe cadastro público: os usuários são criados pela linha de comando. As migrations rodam sozinhas quando a API inicia.

O guia completo, com backup, restauração, atualização e build das imagens a partir do código, está em [docs/instalacao.md](docs/instalacao.md).

> **Cookie seguro.** Com `PRUMO_COOKIE_SECURE=true` (o padrão), o navegador só envia o cookie de sessão por HTTPS, então o login pela web não funciona por `http://` fora de `localhost`. Use um proxy com TLS ou, só numa rede de confiança, `PRUMO_COOKIE_SECURE=false`. O app Android usa token e não depende do cookie.

## Desenvolvimento

Requisitos: Docker, [uv](https://docs.astral.sh/uv/), Node.js 26 com pnpm 12 e make.

```bash
cp .env.example .env
(cd backend && uv sync) && (cd frontend && pnpm install)
make dev        # PostgreSQL no Docker, API com reload (:8000) e Vite (:5173)
make user       # cria o primeiro usuário, em outro terminal
make check      # lint, tipos, testes e o snapshot do OpenAPI (o mesmo do CI)
```

Acesse `http://localhost:5173`. A vitrine de componentes fica em `/dev/ui` e a documentação interativa da API em `/api/docs`. `make screenshots` captura todas as telas com o Playwright e monta comparativos com o design. Os demais comandos (migrations, OpenAPI, backup) estão em [docs/desenvolvimento.md](docs/desenvolvimento.md).

## Estrutura do repositório

```
prumo/
├── backend/     API FastAPI (pacote prumo), migrations e testes
├── frontend/    SPA Vue 3
├── design/      Exportações do design (só referência visual)
├── openapi/     Snapshot do contrato da API
├── deploy/      Dockerfiles, configuração do nginx e scripts de backup
└── docs/        Documentação técnica
```

## Documentação

- [Arquitetura](docs/arquitetura.md)
- [API](docs/api.md)
- [Domínio e regras de negócio](docs/dominio.md)
- [Frontend e design system](docs/frontend.md)
- [Desenvolvimento](docs/desenvolvimento.md)
- [Instalação e atualização](docs/instalacao.md)
- [Criando um módulo](docs/novo-modulo.md)
- [Decisões técnicas](docs/decisoes.md)
- [Histórico de mudanças](CHANGELOG)

## Contribuindo

Issues e sugestões são bem-vindas. Antes de abrir um pull request, leia os guias de arquitetura e de desenvolvimento. Ideias de módulos novos podem começar como uma issue.

## Licença

[GNU Affero General Public License v3.0 ou posterior](LICENSE) (`AGPL-3.0-or-later`). Se você modificar o Prumo e oferecê-lo a outras pessoas pela rede, precisa disponibilizar a elas o código-fonte modificado.

---

Feito por [Henrique Sebastião](https://henriquesebastiao.com).
