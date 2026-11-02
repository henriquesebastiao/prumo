# Roadmap

As fases são executadas em ordem e cada uma termina com uma revisão antes da próxima começar. Um item só é marcado como concluído quando o `make check` está verde e a documentação afetada foi atualizada.

## Fase 0 — Fundação

### Repositório e ferramentas
- [x] Mover a exportação atual de `design/` para `design/v1/` (sem alterar arquivos) e criar `design/README.md` indicando a versão ativa
- [ ] Estrutura de pastas: `backend/`, `frontend/`, `deploy/`, `openapi/`
- [ ] `Makefile` com os comandos listados no `CLAUDE.md`
- [ ] `docker-compose.yml` (db, api, web) e `.env.example`; compose de desenvolvimento só com o banco
- [ ] Scripts de backup e restauração do PostgreSQL
- [ ] CI: lint, typecheck, testes com PostgreSQL, verificação do snapshot OpenAPI e build

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
- [ ] Projeto Vue 3 + TS + Vite com ESLint, Prettier, Stylelint e Vitest
- [ ] Tokens extraídos de `design/v1/` (temas claro e escuro) e seção "Design system atual" de `docs/frontend.md` preenchida
- [ ] Componentes base em `src/ui/` e vitrine `/dev/ui`
- [ ] Cliente da API tipado, gerado do OpenAPI
- [ ] i18n `pt-BR` e formatadores (moeda, km, litros, datas)
- [ ] Registro de módulos (rotas, navegação, widgets do Início, ações rápidas, traduções)
- [ ] AppShell (navegação, alternância de tema, menu do usuário), Login, Início vazio e Configurações (perfil, tema, módulos, sessões, senha)
- [ ] Estados de carregando, vazio e erro
- [ ] Comparação por screenshot (Playwright) com `design/v1/`

## Fase 1 — Veículos (`garage`)

### Backend
- [ ] Veículos: CRUD e arquivamento
- [ ] Odômetro: leituras, consistência cronológica e km atual
- [ ] Oficinas: busca para autocompletar e criação implícita
- [ ] Manutenções com itens (peças) e total calculado
- [ ] Troca de óleo: sugestão da próxima e status (ok, em breve, atrasada)
- [ ] Abastecimentos: preço por litro e consumo pelo método do tanque cheio
- [ ] Detalhe do veículo com informações rápidas e resumo do módulo para o Início

### Frontend
- [ ] Lista de veículos, cadastro e edição
- [ ] Detalhe com informações rápidas e histórico em abas
- [ ] Formulários: atualizar km, manutenção, troca de óleo, abastecimento
- [ ] Widget do Início e ações rápidas
- [ ] Revisão visual contra `design/v1/`

## Fase 2 — Finanças (`finance`)
- [ ] Contas e saldos
- [ ] Categorias: padrões criadas por usuário e CRUD
- [ ] Transações: receita, despesa, transferência; filtros e busca
- [ ] Cartões de crédito: faturas, limite disponível e pagamento
- [ ] Visão geral do mês com gráficos
- [ ] Widget do Início e ações rápidas
- [ ] Revisão visual contra `design/v1/`
- [ ] Compras parceladas no cartão

## Fase 3 — Livros (`reading`)
- [ ] Livros: CRUD, status de leitura e "tenho / não tenho"
- [ ] Progresso de leitura com histórico
- [ ] Anotações por livro
- [ ] Upload de capa
- [ ] Widget do Início e ações rápidas
- [ ] Revisão visual contra `design/v1/`

## Fase 4 — Versão 0.1 (self-host)
- [ ] Imagens Docker publicadas
- [ ] Guia de instalação e atualização
- [ ] Exportação dos dados do usuário (JSON e CSV)
- [ ] Revisão de responsividade (tablet e celular) e de acessibilidade
- [ ] Testes E2E dos fluxos principais com Playwright
- [ ] Licença escolhida e arquivo `LICENSE`
- [ ] README em inglês

## Fase 5 — Preparação para o Android
- [ ] Criação idempotente: aceitar `id` gerado pelo cliente nos `POST`
- [ ] Sincronização incremental: `updated_since` e registro de exclusões
- [ ] Revisão do contrato v1 e início do `CHANGELOG` da API
- [ ] Repositório `prumo-android` (Material 3 Expressive, design system Henrique Sebastião — Android Design System)

## Ideias (sem ordem definida)

- Integração Veículos → Finanças: abastecimentos e manutenções geram despesas automaticamente (via eventos)
- Lembretes de troca de óleo e vencimento de fatura (e-mail ou ntfy)
- Veículos: documentos e vencimentos (IPVA, licenciamento, seguro), pneus, posto no abastecimento, custo por km, consumo por tipo de combustível
- Finanças: transações recorrentes, orçamento por categoria, subcategorias, importação OFX/CSV, metas, múltiplas moedas
- Livros: busca por ISBN, estatísticas e meta anual de leitura, formato (físico ou e-book), empréstimos
- Sistema: autenticação em dois fatores, administração de usuários pela web, dados compartilhados entre usuários, novos módulos
