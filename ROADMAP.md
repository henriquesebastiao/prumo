# Roadmap

As fases são executadas em ordem e cada uma termina com uma revisão antes da próxima começar. Um item só é marcado como concluído quando o `make check` está verde e a documentação afetada foi atualizada.

## Fase 0 — Fundação

### Repositório e ferramentas
- [x] Mover a exportação atual de `design/` para `design/v1/` (sem alterar arquivos) e criar `design/README.md` indicando a versão ativa
- [x] Estrutura de pastas: `backend/`, `frontend/`, `deploy/`, `openapi/`
- [x] `Makefile` com os comandos listados no `CLAUDE.md`
- [x] `docker-compose.yml` (db, api, web) e `.env.example`; compose de desenvolvimento só com o banco
- [x] Scripts de backup e restauração do PostgreSQL
- [x] CI: lint, typecheck, testes com PostgreSQL, verificação do snapshot OpenAPI e build

### Backend
- [x] Configuração (pydantic-settings, prefixo `PRUMO_`), engine e sessão, Alembic
- [x] Base de modelos: UUID v7, `created_at`/`updated_at`, mixin de dono (`user_id`)
- [x] Erros padronizados, paginação, `GET /api/health`
- [x] Contrato `PrumoModule`, registro de módulos, `GET /api/v1/modules` e agregador `GET /api/v1/dashboard`
- [x] Barramento de eventos em processo (mínimo, testado com um módulo falso)
- [x] `import-linter` com o contrato de isolamento entre módulos
- [x] Usuários e CLI (`prumo users create`, `prumo users set-password`)
- [x] Autenticação por sessão: login web (cookie) e app (bearer), logout, `me`, listar e revogar sessões, limite de tentativas
- [x] Preferências do usuário (tema, idioma, fuso, moeda, módulos ativos e ordem)
- [x] `operation_id` estáveis, exportação do OpenAPI e teste de snapshot

### Frontend
- [x] Projeto Vue 3 + TS + Vite com ESLint, Prettier, Stylelint e Vitest
- [x] Tokens extraídos de `design/v1/` (temas claro e escuro) e seção "Design system atual" de `docs/frontend.md` preenchida
- [x] Componentes base em `src/ui/` e vitrine `/dev/ui`
- [x] Cliente da API tipado, gerado do OpenAPI
- [x] i18n `pt-BR` e formatadores (moeda, km, litros, datas)
- [x] Registro de módulos (rotas, navegação, widgets do Início, ações rápidas, traduções)
- [x] AppShell (navegação, alternância de tema, menu do usuário), Login, Início vazio e Configurações (perfil, tema, módulos, sessões, senha)
- [x] Estados de carregando, vazio e erro
- [x] Comparação por screenshot (Playwright) com `design/v1/`

## Fase 1 — Veículos (`garage`)

### Backend
- [x] Veículos: CRUD e arquivamento
- [x] Odômetro: leituras, consistência cronológica e km atual
- [x] Oficinas: busca para autocompletar e criação implícita
- [x] Manutenções com itens (peças) e total calculado
- [x] Troca de óleo: sugestão da próxima e status (ok, em breve, atrasada)
- [x] Abastecimentos: preço por litro e consumo pelo método do tanque cheio
- [x] Detalhe do veículo com informações rápidas e resumo do módulo para o Início
- [x] Extras do design (D27): combustível habitual, óleo utilizado, ritmo de uso, km do mês, histórico de consumo, listas entre veículos e oficinas
- [x] "Vem aí" e "Atividade recente" no dashboard (D28)

### Frontend
- [x] Lista de veículos, cadastro e edição
- [x] Detalhe com informações rápidas e histórico em abas
- [x] Formulários: atualizar km, manutenção, troca de óleo, abastecimento
- [x] Widget do Início e ações rápidas
- [x] Revisão visual contra `design/v1/`
- [x] Abas Abastecimentos, Manutenções, Trocas de óleo e Oficinas; detalhe da manutenção
- [x] "Vem aí" e "Atividade recente" no Início

## Fase 2 — Finanças (`finance`)
- [x] Contas e saldos
- [x] Categorias: padrões criadas por usuário e CRUD
- [x] Transações: receita, despesa, transferência; filtros e busca
- [x] Cartões de crédito: faturas, limite disponível e pagamento
- [x] Visão geral do mês com gráficos
- [x] Widget do Início e ações rápidas
- [x] Revisão visual contra `design/v1/`
- [x] Compras parceladas no cartão

## Fase 3 — Livros (`reading`)
- [x] Livros: CRUD, status de leitura e "tenho / não tenho"
- [x] Progresso de leitura com histórico
- [x] Anotações por livro
- [x] Upload de capa
- [x] Widget do Início e ações rápidas
- [x] Revisão visual contra `design/v1/`

## Fase 4 — Versão 0.1 (self-host)
- [ ] Imagens Docker publicadas (workflow `release.yml` pronto; publica na primeira tag `0.1.0`)
- [x] Guia de instalação e atualização
- [x] Documentação interativa da API (`/api/docs`) sem CDN: servir os arquivos do Swagger UI pela própria instância
- [x] Exportação dos dados do usuário (JSON e CSV)
- [x] Revisão de responsividade (tablet e celular) e de acessibilidade
- [x] Testes E2E dos fluxos principais com Playwright
- [x] Licença escolhida e arquivo `LICENSE`
- [x] README em inglês

## Fase 5 — Preparação para o Android
- [x] Criação idempotente: aceitar `id` gerado pelo cliente nos `POST`
- [x] Sincronização incremental: `updated_since` e registro de exclusões
- [x] Revisão do contrato v1 e início do `CHANGELOG` da API (mudanças no `CHANGELOG` do projeto, D42)
- [x] Repositório `prumo-android` (Material 3 Expressive, design system Henrique Sebastião — Android Design System; em outra sessão, D42). O andamento do app fica no `ROADMAP.md` de lá
- [x] Fluxo de trabalho conjunto com o app: seção "Servidor e app juntos" no `CLAUDE.md` e `commit-message.md` (D43)
- [x] `service: "prumo"` no `GET /api/health`, para o app reconhecer um servidor Prumo (D44)

## Fase 6 — Estudos (`studies`)
Aprovado em 2026-11-10 (D46). Áreas, matérias com link do Obsidian, tópicos criados pelo nome, plano semanal versionado e sessões; dia, semana e Início calculados no servidor.
- [x] Backend: models, migration com os gatilhos de exclusão, API, resumo do Início, "Atividade recente", exportação e testes
- [x] Frontend: Hoje, Semana, Matérias, Plano, diálogos (área, matéria, plano, sessão), widget e ação rápida "Registrar estudo" (atalho E)
- [x] Dados no `e2e_server.py` e capturas em `frontend/e2e/` (`studies-*.png`, claro e escuro, e `responsive/studies-*`); `make check` verde em 2026-11-11

## Fase 7 — Hábitos (`habits`)
Aprovado em 2026-11-10 (D47), para depois de alguns dias de uso de Estudos. Hábitos a praticar (`check` ou quantidade; diário, X por semana ou dias da semana, com vigência) e a abandonar (recaídas e dias sem).
- [x] Backend: models, migration, API (marcação por `PUT` por data), calendário do mês, resumo do Início, exportação e testes
- [x] Frontend: Hoje, Hábitos, detalhe com calendário, diálogos (hábito, frequência, pausa, recaída), widget e ação rápida "Marcar hábitos" (atalho H)
- [x] Dados no `e2e_server.py` e capturas em `frontend/e2e/` (`habits-*.png`, claro e escuro, e `responsive/habits-*`); `make check` verde em 2026-11-11

## Ideias (sem ordem definida)

- Integração Veículos → Finanças: abastecimentos e manutenções geram despesas automaticamente (via eventos)
- Lembretes de troca de óleo e vencimento de fatura (e-mail ou ntfy)
- Veículos: documentos e vencimentos (IPVA, licenciamento, seguro), pneus, posto no abastecimento, custo por km, consumo por tipo de combustível
- Finanças: transações recorrentes, orçamento por categoria, subcategorias, importação OFX/CSV, metas, múltiplas moedas
- Livros: busca por ISBN, estatísticas e meta anual de leitura, formato (físico ou e-book), empréstimos
- Sistema: autenticação em dois fatores, administração de usuários pela web, dados compartilhados entre usuários, novos módulos
