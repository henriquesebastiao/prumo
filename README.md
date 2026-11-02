# Prumo

Organização pessoal modular e self-hosted: veículos, finanças, leituras e o que mais vier, rodando no seu próprio servidor.

> "Estar no prumo" é estar em ordem, alinhado. É o que o Prumo tenta fazer pela rotina: um lugar só, sob o seu controle, para registrar e acompanhar as coisas do dia a dia.

**Status:** em desenvolvimento inicial. Ainda não está pronto para uso; acompanhe pelo [ROADMAP](ROADMAP.md).

## O que ele faz

**Veículos.** Carros e motos com quilometragem atualizável a qualquer momento; manutenções com peças, valores, mão de obra e oficina; trocas de óleo com cálculo automático da próxima, por km ou por data; abastecimentos com preço por litro e consumo médio; um painel rápido de cada veículo.

**Finanças.** Contas e saldos; receitas, despesas e transferências; categorias personalizáveis; cartões de crédito com faturas, limite disponível e pagamento; visão geral do mês.

**Livros.** Os livros que você tem, está lendo e quer ler; progresso de leitura com histórico; anotações por livro.

**E o que vier depois.** Cada área da vida é um módulo independente. Módulos novos entram sem mexer nos existentes, e cada pessoa ativa só os que usa.

## Princípios

- **Seus dados, seu servidor.** Self-hosted, sem serviços de terceiros, com backup simples do banco.
- **API primeiro.** Tudo o que a interface web faz passa por uma API documentada. O app Android usa a mesma API.
- **Modular.** Módulos isolados, com o mesmo contrato no backend e no frontend.
- **Multiusuário por instância.** Uma instalação pode atender mais de uma pessoa, cada uma com os próprios dados.
- **Design substituível.** A aparência vive em tokens e em uma biblioteca de componentes própria, para que a interface evolua sem reescrever telas.

## Stack

| Camada | Tecnologia |
|---|---|
| API | Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Banco | PostgreSQL |
| Web | Vue 3, TypeScript, Vite, Vue Router, TanStack Query, vue-i18n, Reka UI |
| Android | Kotlin, Jetpack Compose, Material 3 Expressive (repositório `prumo-android`, em breve) |
| Implantação | Docker Compose, nginx |

## Instalação (self-host)

> Disponível a partir da versão 0.1. Os comandos abaixo descrevem o fluxo planejado.

```bash
git clone <url-do-repositorio> prumo
cd prumo
cp .env.example .env          # defina senhas, porta e fuso horário
docker compose up -d
docker compose exec api prumo users create --admin
```

Acesse `http://<seu-servidor>:<PRUMO_PORT>`. Para HTTPS, publique a porta através do seu proxy reverso. Não existe cadastro público: novos usuários são criados pela linha de comando.

> **Cookie seguro.** Com `PRUMO_COOKIE_SECURE=true` (o padrão), o navegador só envia o cookie de sessão por HTTPS, então o login pela web não funciona acessando o Prumo por `http://` (exceto em `localhost`). Use um proxy reverso com TLS ou, só numa rede de confiança, defina `PRUMO_COOKIE_SECURE=false`. O app Android não depende de cookie.
>
> **Senha do banco.** `POSTGRES_PASSWORD` entra na URL de conexão da API: use letras, números, `-` e `_`, ou codifique os demais caracteres (`@` vira `%40`).

O backup é um dump do PostgreSQL (`make backup`); veja [docs/desenvolvimento.md](docs/desenvolvimento.md).

## Desenvolvimento

Requisitos: Docker, [uv](https://docs.astral.sh/uv/), Node.js 26 (LTS) com pnpm 12 e make.

```bash
cp .env.example .env
(cd backend && uv sync) && (cd frontend && pnpm install)
make dev        # banco no Docker, API com reload e frontend com Vite
make user       # cria o primeiro usuário
make check      # lint, tipos e testes
```

O guia completo está em [docs/desenvolvimento.md](docs/desenvolvimento.md).

## Estrutura

```
prumo/
├── backend/     API FastAPI (pacote prumo), migrations e testes
├── frontend/    SPA Vue 3
├── design/      Exportações do design (referência visual)
├── openapi/     Snapshot do contrato da API
├── deploy/      Dockerfiles, nginx e scripts
└── docs/        Documentação técnica
```

## Documentação

- [Arquitetura](docs/arquitetura.md)
- [API](docs/api.md)
- [Domínio e regras de negócio](docs/dominio.md)
- [Frontend e design](docs/frontend.md)
- [Desenvolvimento](docs/desenvolvimento.md)
- [Como criar um módulo](docs/novo-modulo.md)
- [Decisões técnicas](docs/decisoes.md)

## Contribuindo

Issues e sugestões são bem-vindas. Antes de abrir um pull request, leia a arquitetura e o guia de desenvolvimento. Ideias de novos módulos podem começar como issue.

## Licença

[GNU Affero General Public License v3.0 ou posterior](LICENSE) (`AGPL-3.0-or-later`). Se você modificar o Prumo e oferecê-lo pela rede a outras pessoas, precisa disponibilizar o código-fonte modificado a elas.

---

Feito por [Henrique Sebastião](https://henriquesebastiao.com).
