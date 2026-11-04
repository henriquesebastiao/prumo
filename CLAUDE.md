# Prumo

Sistema open source e self-hosted de organização pessoal, dividido em módulos (Veículos, Finanças, Livros e outros no futuro). Este repositório contém a API (FastAPI) e o frontend web (Vue). O app Android fica em outro repositório (`prumo-android`) e consome a mesma API.

O estado atual e a próxima tarefa estão sempre no `ROADMAP.md`.

## Mapa do repositório

- `backend/`: API FastAPI (pacote `prumo`, layout `src/`), migrations Alembic, testes pytest
- `frontend/`: SPA Vue 3 + TypeScript + Vite
- `design/`: exportações do Claude Design (HTML + imagens), versionadas em `design/v1/`, `design/v2/`… É **somente referência visual**: nunca importe nada daqui no código
- `openapi/openapi.json`: snapshot do contrato da API (gerado e versionado)
- `deploy/`: Dockerfiles, configuração do nginx, scripts de backup
- `docs/`: documentação técnica

## Leia antes de trabalhar em…

- Estrutura do backend ou do sistema de módulos: `docs/arquitetura.md`
- Um módulo novo: `docs/novo-modulo.md`
- Endpoints, autenticação, formatos de dados e erros: `docs/api.md`
- Regras de negócio e modelo de dados: `docs/dominio.md`
- Telas, componentes, tokens ou redesign: `docs/frontend.md`
- Setup, comandos, testes e migrations: `docs/desenvolvimento.md`
- Instalação, atualização e publicação de versões: `docs/instalacao.md`
- O porquê de uma escolha: `docs/decisoes.md`

## Comandos

Criados na Fase 0. Mantenha esta lista em sincronia com o `Makefile`.

- `make dev`: PostgreSQL no Docker + API com reload + Vite
- `make check`: lint + typecheck + testes (backend e frontend) + verificação do snapshot OpenAPI. Rode antes de considerar qualquer tarefa pronta
- `make test`, `make lint`, `make typecheck`, `make format`
- `make db-up` / `make db-down`: bancos de desenvolvimento e de testes
- `make screenshots`: Playwright captura as telas e monta comparativos com a versão ativa de `design/` em `frontend/e2e/output/compare/`
- `make migration m="descricao"`: gera migration Alembic (revise sempre o arquivo gerado)
- `make migrate`: aplica as migrations
- `make openapi`: exporta `openapi/openapi.json` e regenera os tipos TypeScript do frontend
- `make user`: cria usuário pela CLI
- `make backup` / `make restore f=<arquivo>`
- `make changelog`: gera o `CHANGELOG` a partir do GitHub (`github_changelog_generator`)

## Regras do projeto

### Arquitetura
- O frontend web é apenas um cliente da API, exatamente como o Android será. Toda regra de negócio, validação de domínio e valor derivado (próxima troca de óleo, consumo, saldos, faturas, progresso de leitura) fica no backend.
- Módulos ficam em `backend/src/prumo/modules/<id>/` e `frontend/src/modules/<id>/`. IDs atuais, na ordem padrão da navegação: `finance` (Finanças), `garage` (Veículos), `reading` (Livros).
- Um módulo importa de `core` e `system`, nunca de outro módulo (exceto o `events.py` público dele). O `import-linter` verifica isso no `make lint`.
- Routers são finos: HTTP, dependências, status code. Regras de negócio ficam em `service.py`.
- Tabelas de módulo usam o id como prefixo: `garage_fuelings`, `finance_accounts`, `reading_books`.

### Dados
- Todo registro pertence a um usuário (`user_id`) e toda consulta filtra por ele. Recurso de outro usuário responde 404, nunca 403.
- Dinheiro em centavos inteiros (sufixo `_cents`), volume em mililitros (`_ml`), distância em km inteiros. Nunca float para dinheiro.
- Data-hora sempre com fuso, armazenada em UTC. Conversão para o fuso do usuário só na borda (cálculos "do mês" e "de hoje" usam o fuso da preferência do usuário).
- IDs são UUID v7.
- Schema só muda via Alembic. Nunca edite uma migration já commitada; crie outra.

### API
- Prefixo `/api/v1`, JSON em snake_case, formatos de erro e paginação padronizados (`docs/api.md`).
- A v1 é um contrato com o app Android: só mudanças aditivas. Qualquer mudança incompatível precisa da minha aprovação.
- Mudou a API? Rode `make openapi` e inclua o snapshot e os tipos regenerados no mesmo commit.

### Frontend e design
- O design vai mudar com o tempo. Um redesign deve exigir mudanças em `src/design/`, `src/ui/` e `src/layouts/`, não nas telas.
- Telas usam apenas componentes de `frontend/src/ui/` e tokens semânticos de `frontend/src/design/`. Nenhuma cor, fonte, sombra ou raio literal fora de `src/design/`.
- O CSS das telas só cuida de layout (grid, flex, gap com tokens de espaço). Aparência é responsabilidade de `src/ui/`.
- Todo texto visível vem do i18n (`pt-BR` por padrão). Nada de string fixa em componente.
- Ícones só via `<PIcon>` (Lucide, mapeado em `src/ui/icons.ts`), gráficos só via `<PChart>`, texto estilizado via `<PText>`.
- Todo componente novo de `src/ui/` entra na vitrine `/dev/ui`, nos dois temas.

### Qualidade
- Toda regra de negócio tem teste de serviço. Todo endpoint tem teste de API, incluindo o caso "outro usuário recebe 404".
- Testes de backend usam PostgreSQL real, nunca SQLite.
- Ao implementar ou alterar uma tela, compare com as imagens da versão ativa em `design/` (screenshot com Playwright).
- Pronto significa: `make check` verde, documentação afetada atualizada, item marcado no `ROADMAP.md` e `commit-message.md` descrevendo a mudança.
- Ambiguidade nos docs durante a execução: escolha a opção mais simples que não feche portas, registre em `docs/decisoes.md` e siga.

### Convenções
- Código, identificadores, commits e comentários em inglês. Documentação e textos de interface em pt-BR.
- Conventional Commits com escopo do módulo (`feat(garage): add fueling endpoints`), escritos em `commit-message.md` e nunca commitados por você (veja "Servidor e app juntos").
- Python: type hints em tudo, ruff (lint e format), mypy. Gerenciador: uv.
- TypeScript em modo strict, `<script setup lang="ts">`, ESLint, Prettier, Stylelint. Gerenciador: pnpm.

### Pergunte antes de
- Adicionar uma dependência que não esteja prevista nos docs
- Contrariar uma decisão registrada em `docs/decisoes.md`
- Fazer uma mudança incompatível na API v1
- Criar migration que apague ou transforme dados existentes

## Servidor e app juntos

O app Android fica em `~/git/prumo-android`; o servidor (API e web), aqui em `~/git/prumo`. Os dois evoluem como um produto só: quando uma tarefa num repositório precisa de uma mudança no outro (um endpoint ou campo novo da v1, um bug do servidor que o app encontrou, documentação de contrato errada), faça a mudança no outro repositório na mesma tarefa, sem parar para perguntar. Uma sessão aberta no app pode mudar este repositório do mesmo jeito.

- Antes de editar o outro repositório, leia o `CLAUDE.md` dele e siga-o lá (ferramentas, testes, documentação, critério de pronto). Uma mudança do servidor de que o app depende leva testes, documentação (`docs/api.md`, `docs/dominio.md`) e o snapshot do OpenAPI na mesma mudança.
- Apps instalados continuam chamando o formato antigo: na v1, só mudanças aditivas. A lista "Pergunte antes de" vale nos dois lados.
- **Não faça commit, stage nem push em nenhum dos dois repositórios.** O mantenedor faz os commits. Exceção: numa sessão na nuvem, em que o trabalho só sobrevive no GitHub, o mantenedor pode pedir commit e push num branch de trabalho, nunca na `main`; o `commit-message.md` continua descrevendo tudo o que está pendente de revisão.
- **Nenhuma mudança sem descrição.** Toda edição em arquivo versionado (código, testes, docs, configuração) é descrita em `commit-message.md` na raiz do repositório que ela tocou (ignorado pelo git nos dois). Uma tarefa que tocou os dois repositórios deixa uma mensagem em cada um, e cada mensagem cita o outro lado ("Needs the server's …" / "Used by the Android app's …").
- Escreva a mensagem antes da resposta final, em inglês e em Conventional Commits com o escopo do módulo: assunto no imperativo com até 72 caracteres, corpo dizendo o porquê e, depois, o que mudou por arquivo ou área.
- O arquivo pode ter uma mensagem antiga. Se o `git log` já tem o assunto dela, ela foi commitada: substitua. Se ela descreve mudanças ainda não commitadas, mantenha: amplie a mensagem para cobrir tudo o que está pendente ou acrescente outra para um trabalho não relacionado, separada por uma linha `---` e citando os arquivos que cobre.
- Termine a resposta final citando cada repositório alterado e o seu `commit-message.md`.
