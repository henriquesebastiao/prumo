# Decisões técnicas

Registro curto das decisões que moldam o projeto. Para mudar uma decisão aceita, adicione uma nova entrada que a substitua (e marque a antiga como substituída) em vez de editar o histórico.

---

## D01 — Monorepo para API e web; Android separado
**Status:** aceita · 2026-11
**Contexto:** API e web evoluem juntas e compartilham o contrato; o Android tem ciclo, ferramentas e build próprios.
**Decisão:** `prumo` contém backend, frontend e docs; `prumo-android` é outro repositório.
**Consequências:** o contrato precisa ser publicado de forma consumível pelo outro repositório (`openapi/openapi.json`).

## D02 — API primeiro: o frontend web é só um cliente
**Status:** aceita · 2026-11
**Contexto:** o Android precisa de exatamente as mesmas funcionalidades e dos mesmos números.
**Decisão:** toda regra de negócio e todo valor derivado ficam no backend. A web não calcula nada que o Android teria que recalcular.
**Consequências:** respostas incluem campos calculados (status de óleo, consumo, saldos, faturas, progresso). Mais trabalho no backend, zero divergência entre clientes.

## D03 — Módulos com registro explícito e isolamento verificado
**Status:** aceita · 2026-11
**Contexto:** o sistema deve receber módulos novos sem mexer nos existentes.
**Decisão:** contrato `PrumoModule` no backend e `defineModule` no frontend; lista explícita de módulos instalados; módulos não importam outros módulos (exceto `events.py` público); `import-linter` garante a regra.
**Consequências:** integrações entre módulos passam por eventos, o que é mais verboso que uma chamada direta, mas mantém módulos removíveis.

## D04 — PostgreSQL em todos os ambientes, inclusive testes
**Status:** aceita · 2026-11
**Contexto:** SQLite diverge do PostgreSQL em tipos, fusos e constraints.
**Decisão:** PostgreSQL em produção, desenvolvimento e testes.
**Consequências:** rodar testes exige Docker. Em troca, o que passa no teste funciona em produção.

## D05 — SQLAlchemy síncrono
**Status:** aceita · 2026-11
**Contexto:** uso pessoal, baixa concorrência; o modo assíncrono traz armadilhas (lazy loading, sessões) sem ganho real aqui.
**Decisão:** SQLAlchemy 2 síncrono com psycopg 3; rotas síncronas, executadas pelo FastAPI em pool de threads.
**Consequências:** código e testes mais simples. Se um dia houver necessidade real de I/O assíncrono, a migração é localizada em `core/db.py` e nos serviços.

## D06 — Tokens de sessão opacos, não JWT
**Status:** aceita · 2026-11
**Contexto:** web e app precisam autenticar; o usuário deve poder ver e revogar dispositivos.
**Decisão:** tokens aleatórios guardados como hash no banco. A web recebe o token em cookie `HttpOnly`; o app, no corpo da resposta, para usar como bearer.
**Consequências:** uma consulta ao banco por requisição (irrelevante nessa escala), revogação imediata e tela de sessões ativas sem complexidade extra.

## D07 — Multiusuário por instância, sem cadastro público
**Status:** aceita · 2026-11
**Contexto:** uma instalação pode servir mais de uma pessoa; adicionar `user_id` depois seria uma migração cara.
**Decisão:** todo dado pertence a um usuário desde o início; usuários são criados pela CLI.
**Consequências:** testes de isolamento obrigatórios em todo endpoint. Compartilhamento entre usuários fica para o futuro.

## D08 — Quantidades em inteiros: centavos, mililitros, km
**Status:** aceita · 2026-11
**Contexto:** float causa erros de arredondamento; decimais em JSON são tratados de forma inconsistente entre clientes.
**Decisão:** dinheiro em centavos (`_cents`), volume em mililitros (`_ml`), distância em km inteiros. Valores derivados de exibição são calculados pelo backend.
**Consequências:** formatação fica nos clientes (`lib/format.ts` na web). Moeda única por usuário por enquanto.

## D09 — UUID v7 como identificador
**Status:** aceita · 2026-11
**Contexto:** IDs sequenciais vazam volume de dados; o Android poderá precisar gerar IDs offline.
**Decisão:** UUID v7 (ordenável por tempo) gerado na aplicação.
**Consequências:** prepara a criação idempotente e a sincronização da Fase 5.

## D10 — Troca de óleo é um tipo de manutenção
**Status:** aceita · 2026-11
**Contexto:** troca de óleo tem oficina, peças e mão de obra como qualquer manutenção, mais a previsão da próxima.
**Decisão:** `Maintenance.kind = oil_change` com campos `next_oil_change_*`, em vez de uma entidade separada.
**Consequências:** custos e histórico unificados; a interface pode oferecer um formulário dedicado que usa o mesmo endpoint.

## D11 — Faturas calculadas, não armazenadas
**Status:** aceita · 2026-11
**Contexto:** guardar faturas exige mantê-las sincronizadas com cada edição de compra.
**Decisão:** cada compra no cartão grava `invoice_closing_on`; faturas são agregadas sob demanda; pagamentos são transações `card_payment`.
**Consequências:** sem estado duplicado. Se o desempenho exigir, uma tabela de cache pode ser adicionada sem mudar a API.

## D12 — Camada visual substituível
**Status:** aceita · 2026-11
**Contexto:** o design atual pode não ser o definitivo.
**Decisão:** tokens primitivos e semânticos em CSS custom properties; biblioteca de componentes própria (`src/ui/`) sobre primitivos headless (Reka UI); telas sem estilo visual próprio; sem framework de CSS utilitário nas telas; vitrine `/dev/ui`.
**Consequências:** um pouco mais de trabalho inicial para criar componentes; um redesign passa a ser troca de tokens e componentes.

## D13 — Uma porta só na implantação
**Status:** aceita · 2026-11
**Contexto:** o servidor de destino publica cada serviço numa porta própria atrás de um proxy reverso.
**Decisão:** nginx no container `web` serve a SPA e encaminha `/api`; só ele é publicado.
**Consequências:** mesma origem para web e API, cookies sem configuração especial, CORS desligado por padrão.

## D14 — Código em inglês, interface em pt-BR via i18n
**Status:** aceita · 2026-11
**Contexto:** projeto open source com público inicial brasileiro.
**Decisão:** identificadores, commits e mensagens técnicas em inglês; textos de interface sempre via i18n, com `pt-BR` padrão; documentação em pt-BR.
**Consequências:** traduzir para outros idiomas não exige mudar código.

## D15 — Licença
**Status:** aceita · 2026-11
**Contexto:** projeto open source e self-hosted, usado como serviço de rede.
**Decisão:** GNU Affero General Public License v3.0 ou posterior (`AGPL-3.0-or-later`), texto em `LICENSE`.
**Consequências:** quem modificar o Prumo e oferecê-lo pela rede a outras pessoas precisa disponibilizar o código-fonte modificado a elas (seção 13). Usar a versão sem modificações não exige nada além de manter a licença.

## D16 — Ícones Lucide atrás de `<PIcon>`
**Status:** aceita · 2026-11
**Contexto:** o design v1 desenha cerca de 45 ícones próprios, no estilo do Lucide (grade 24, traço 2), mas módulos futuros vão precisar de muitos outros.
**Decisão:** Lucide (`@lucide/vue`), importado apenas em `src/ui/icons.ts`, que mapeia nomes semânticos (`car`, `wallet`, `fuel`…) para os componentes. Telas usam só `<PIcon name>`; o ESLint proíbe importar Lucide fora de `src/ui/`.
**Consequências:** os ícones não são idênticos aos do design, só parecidos. Trocar o conjunto é editar um arquivo.

## D17 — Gráficos próprios, sem biblioteca
**Status:** aceita · 2026-11
**Contexto:** o design só usa formas simples (barras com média, barras agrupadas, rosca, barra empilhada, anéis).
**Decisão:** `<PChart>` implementado em CSS e SVG, com tokens e tons, descrição acessível e lista de valores para leitores de tela.
**Consequências:** nenhuma dependência pesada e fidelidade total ao design. Se surgir um gráfico complexo (séries temporais com zoom, por exemplo), uma biblioteca pode entrar atrás do mesmo componente.

## D18 — Figtree hospedada pela aplicação
**Status:** aceita · 2026-11
**Contexto:** o design usa Figtree (Google Fonts); o Prumo não deve depender de serviços de terceiros em tempo de execução.
**Decisão:** `@fontsource-variable/figtree`, empacotada no build pelo Vite.
**Consequências:** a fonte vai junto com a SPA; nenhuma requisição externa.

## D19 — "Manter conectado" na web
**Status:** aceita · 2026-11
**Contexto:** o design de login tem a opção "Manter conectado neste dispositivo"; a API previa sessão web fixa de 30 dias.
**Decisão:** campo aditivo `remember` no login (padrão `true`). Marcado: sessão de `PRUMO_SESSION_DAYS_WEB` dias e cookie persistente. Desmarcado: sessão de `PRUMO_SESSION_HOURS_WEB_TRANSIENT` horas (12) e cookie de sessão do navegador. O app ignora o campo.
**Consequências:** nenhuma mudança incompatível; um computador compartilhado não fica conectado por um mês.

## D20 — Preferência de módulos guardada como ordem + desativados
**Status:** aceita · 2026-11
**Contexto:** guardando só a lista de módulos ativos, um módulo instalado depois nasceria desativado para os usuários existentes.
**Decisão:** o banco guarda `module_order` e `disabled_modules`; a API continua expondo `enabled_modules` (lista ordenada). Módulos que não estão na ordem salva aparecem no fim, ativos.
**Consequências:** instalar um módulo o mostra a todos; desativar continua sendo escolha de cada usuário.

## D21 — `CurrentUser` fica em `system`, não em `core`
**Status:** aceita · 2026-11
**Contexto:** a arquitetura previa `SessionDep` e `CurrentUser` em `core/deps.py`, mas o usuário e as sessões são modelos de `system`, e `core` não pode importar `system`.
**Decisão:** `SessionDep` em `prumo.core.deps`; `CurrentUser` e `CurrentAuth` em `prumo.system.auth.deps`. O registro de módulos e o barramento de eventos são instâncias em `core` preenchidas por `prumo.main.bootstrap()`, que também injeta a checagem de módulo ativo no barramento.
**Consequências:** módulos importam `CurrentUser` de `prumo.system.auth.deps` (permitido). O import-linter garante a direção.

## D22 — Conflitos do design v1 com os docs na Fase 0
**Status:** aceita · 2026-11
**Contexto:** o design de login e configurações tem elementos sem base no domínio.
**Decisão:** login só por usuário (sem e-mail; a recuperação continua pelo terminal); sem foto de perfil (avatar com iniciais); usuário visível mas não editável; tema guardado na conta (preferência do servidor), com o texto da tela ajustado; sem busca global por enquanto; "Sair" na cor de texto, como aparece no design. No celular, barra inferior com FAB (como no design) em vez de gaveta.
**Consequências:** cada item pode voltar como mudança aditiva da API quando for desejado. As divergências dos módulos estão listadas em `docs/frontend.md` e são decididas na fase de cada um.

## D23 — Formatos pequenos da API
**Status:** aceita · 2026-11
**Contexto:** algumas coleções são pequenas e não paginam; o login atende dois tipos de cliente.
**Decisão:** coleções sem paginação (`/modules`, `/auth/sessions`) respondem `{ "items": [...] }`, extensível de forma aditiva. O login tem um schema único, `LoginResponse`, com `token` anulável (só vem para `client: "app"`) e `expires_at`. Mutação por cookie sem `X-Prumo-Client: web` responde `403 auth.client_header_required`.
**Consequências:** clientes gerados têm tipos simples; nenhuma união por tipo de cliente.

## D24 — Limite de tentativas de login no banco
**Status:** aceita · 2026-11
**Contexto:** o limite precisa valer para todos os workers e reinícios da API.
**Decisão:** tabela `login_attempts` (usuário normalizado, IP, sucesso, horário). Cinco falhas dentro de 15 minutos, sem sucesso depois delas, bloqueiam o par usuário + IP por 15 minutos a partir da última falha (`429 auth.rate_limited` com `Retry-After`). Linhas com mais de um dia são apagadas a cada login. Usuário inexistente gasta o mesmo tempo de verificação de senha.
**Consequências:** sem Redis nem estado em memória. O IP vem do nginx (`X-Forwarded-For`, confiado pelo Uvicorn).

## D25 — Versões de ferramentas fora do mais recente
**Status:** aceita · 2026-11
**Contexto:** algumas versões estáveis mais novas ainda não funcionam com o resto do ecossistema.
**Decisão:** TypeScript 6.0 (o 7.0 é o port nativo, e o `typescript-eslint` ainda exige < 6.1). Testes de backend usam `httpx2`, que o Starlette 1.10 passou a recomendar no `TestClient` no lugar do `httpx`.
**Consequências:** revisar quando o `typescript-eslint` aceitar o TypeScript 7.

## D26 — Fatura segue a regra F4, não o design v1
**Status:** aceita · 2026-11
**Contexto:** a prancha "Cartões de crédito" mostra, para fechamento no dia 3, "lançamentos de 04/11 a 03/12", o que inclui a compra feita no dia do fechamento.
**Decisão:** vale F4: a compra no dia do fechamento cai na fatura seguinte (no exemplo, lançamentos de 03/11 a 02/12). A interface mostra o período calculado pela API.
**Consequências:** o texto da prancha é tratado como erro do design.

## D27 — Extras do design v1 em Veículos
**Status:** aceita · 2026-11
**Contexto:** o design v1 mostra dados que o domínio não tinha (G1–G8 da análise da Fase 0).
**Decisão:** entram no domínio e na API: combustível habitual do veículo, óleo utilizado na troca (com sugestões), ritmo de uso com data estimada (G12), km rodados no mês (G13), histórico de consumo, listas de manutenções e abastecimentos entre veículos, oficinas com estatísticas, quantidade por peça (padrão 1) e mão de obra separada (exibida como linha "Serviço" só na interface).
**Consequências:** mais valores derivados no backend, iguais para web e Android.

## D28 — "Vem aí" e "Atividade recente" no dashboard
**Status:** aceita · 2026-11
**Contexto:** o Início do design agrega eventos de vários módulos.
**Decisão:** `PrumoModule` ganha os provedores opcionais `upcoming` e `activity`, que devolvem itens genéricos (`UpcomingItem`, `ActivityItem`: `module`, `kind`, data ou horário, `subject`, `entity_id`, `data`). O dashboard junta os itens dos módulos ativos, ordena e limita (10 itens; `upcoming` até 60 dias à frente). Os clientes traduzem cada `kind`.
**Consequências:** mudança aditiva no `GET /dashboard`. Cada módulo documenta os seus `kind` e os campos de `data` em `docs/api.md`.

## D29 — Regras de odômetro e oficinas na implementação
**Status:** aceita · 2026-11
**Contexto:** pontos que o domínio deixava em aberto.
**Decisão:** o km do formulário de edição do veículo registra uma leitura manual; a última leitura não pode ser excluída; o vão do intervalo de óleo é medido da última troca até a próxima prevista (respeita valores alterados pelo usuário); oficina com manutenções não pode ser excluída; o lint ignora `FAST003` porque parâmetros de caminho costumam ser consumidos por dependências (`VehicleDep`).
**Consequências:** regras G2, G3, G6 e G10 detalhadas em `docs/dominio.md`.

## D30 — Dados de demonstração das pranchas
**Status:** aceita · 2026-11
**Contexto:** comparar telas de módulo com o design exige muitos dados coerentes (km, trocas, abastecimentos) e "hoje" fixo; simular toda a API no navegador seria frágil.
**Decisão:** `backend/scripts/e2e_server.py` cria um banco descartável, semeia os dados das pranchas pelos serviços (regras reais) e serve a API com o relógio congelado no momento do design. O Playwright o inicia junto com o Vite.
**Consequências:** as capturas exercitam o backend de verdade. Cada módulo novo acrescenta seus dados ao script.

## D31 — Divergências do design v1 em Finanças
**Status:** aceita · 2026-11
**Contexto:** as pranchas de Finanças mostram dados e ações que o domínio não previa.
**Decisão:** transação ganha hora opcional (`occurred_time`, só para exibir e ordenar no dia; relatórios usam `occurred_on`); categorias padrão automáticas (F7), sem o botão "Usar categorias sugeridas"; o formulário de conta pede o saldo inicial e "Ajustar saldo" cria uma transação `adjustment` com a diferença (F11), fora de receitas, despesas e relatórios; a visão geral traz a série de 6 meses (F12) e navega entre meses; a busca aceita valor (F13); "Combustível" entra nas categorias padrão; contas informam última movimentação e transações do mês (F14).
**Consequências:** mais valores derivados no backend; a interface só exibe.

## D32 — Exclusão de categorias, contas e cartões
**Status:** aceita · 2026-11
**Contexto:** a prancha "Categorias" mostra "Excluir" deixando as transações sem categoria; isso quebraria F3 (relatórios por categoria) e a regra de que toda receita e despesa tem categoria.
**Decisão:** categoria, conta ou cartão com transações não podem ser excluídos, só arquivados (F8). A interface troca "Excluir" por "Arquivar" quando há uso.
**Consequências:** histórico sempre íntegro; itens arquivados saem dos seletores.

## D33 — Saldos, tipo da transação e descrição
**Status:** aceita · 2026-11
**Contexto:** pontos que o domínio deixava em aberto.
**Decisão:** o saldo de uma conta considera as transações até hoje (no fuso do usuário); a visão geral de um mês passado ou futuro usa o último dia daquele mês. O limite do cartão considera todas as compras, inclusive parcelas futuras. O `kind` de uma transação não muda depois de criada (para trocar, exclua e crie outra). A descrição é obrigatória em receitas e despesas e opcional (vazia) em transferências, pagamentos e ajustes, que os clientes rotulam pelo tipo. Um número inteiro na busca encontra os valores com aqueles reais (212 → de 212,00 a 212,99). Cores são chaves de uma paleta fixa; ícones são nomes livres (`[a-z0-9-]`), e o cliente usa um ícone genérico quando não conhece o nome.
**Consequências:** lançamentos agendados não alteram o saldo de hoje; as categorias padrão nascem em pt-BR (dados do usuário, editáveis).

## D34 — Totais na lista de transações
**Status:** aceita · 2026-11
**Contexto:** a prancha "Transações" mostra, para os filtros aplicados, a quantidade e os totais de receitas e despesas.
**Decisão:** `GET /finance/transactions` devolve o formato padrão de página mais `income_cents` e `expense_cents` do filtro inteiro (não só da página). `GET /finance/accounts` devolve `{items, total_balance_cents}`.
**Consequências:** extensão aditiva do formato de lista, documentada em `docs/api.md`.

## D35 — Divergências do design v1 em Livros
**Status:** aceita · 2026-11
**Contexto:** as pranchas de Livros mostram dados que o domínio não tinha.
**Decisão:** entram no domínio e na API: ritmo de leitura e previsão de término (R7, R8), páginas por semana (R9), a aba "Anotações" com todas as anotações (`GET /reading/notes`), a data editável da anotação (`noted_on`) e o "tenho" no cadastro, como selo na estante e como filtro.
**Consequências:** valores derivados no backend, iguais para web e Android; `ReadingProgress` guarda a página anterior para medir o avanço.

## D36 — Processamento da capa
**Status:** aceita · 2026-11
**Contexto:** R6 pede upload `multipart/form-data` e redimensionamento no servidor.
**Decisão:** dependências `python-multipart` (uploads no FastAPI) e Pillow. A imagem é validada pelo conteúdo, tem a orientação EXIF aplicada, é reduzida a 800 px no maior lado e regravada em WebP em `PRUMO_UPLOADS_DIR/reading/covers/<id do livro>.webp`.
**Consequências:** metadados (como GPS) não ficam guardados; o backup inclui o volume de uploads.

## D37 — Publicação das imagens
**Status:** aceita · 2026-11
**Contexto:** a versão 0.1 pede imagens Docker publicadas.
**Decisão:** GitHub Container Registry (`ghcr.io/henriquesebastiao/prumo-api` e `prumo-web`), publicadas pelo GitHub Actions quando uma tag de versão sem prefixo (`0.1.0`) chega ao repositório. Cada versão gera as tags `0.1.0`, `0.1` e `latest`, para amd64 e arm64. O `docker-compose.yml` usa essas imagens; `docker-compose.build.yml` constrói localmente.
**Consequências:** quem instala não precisa do código-fonte; a tag do git é a versão.

## D38 — Exportação dos dados do usuário
**Status:** aceita · 2026-11
**Contexto:** a versão 0.1 pede exportação em JSON e CSV.
**Decisão:** `GET /api/v1/me/export` devolve um `.zip` com `data.json` (perfil, preferências e os dados de cada módulo ativo ou não), um CSV por tabela (`<módulo>/<tabela>.csv`) e os arquivos enviados (capas). Não inclui senha, sessões nem tentativas de login. Cada módulo declara o que exporta (`PrumoModule.export`).
**Consequências:** o usuário leva os próprios dados sem acesso ao servidor; a importação fica para depois.

## D39 — Swagger UI sem CDN
**Status:** aceita · 2026-11
**Contexto:** o FastAPI carrega o Swagger UI do jsDelivr. O pacote `swagger-ui-bundle` traz só o Swagger UI 4, que não abre OpenAPI 3.1.
**Decisão:** os arquivos do `swagger-ui-dist` 5 (bundle, CSS, favicon, licença) ficam em `backend/src/prumo/static/swagger-ui/`, copiados por `backend/scripts/update-swagger-ui.sh` com versão e checksum fixos, e a API os serve em `/api/docs/static`.
**Consequências:** `/api/docs` funciona offline; atualizar é rodar o script com a nova versão.

## D40 — Criação idempotente
**Status:** aceita · 2026-11
**Contexto:** o app Android precisa repetir criações depois de falhas de rede sem duplicar registros.
**Decisão:** os `POST` de criação aceitam `id` (UUID v7) do cliente. Repetir com o mesmo `id`, o mesmo usuário e o mesmo recurso devolve `200` com o registro existente, sem comparar o corpo; `id` de outro usuário responde `409 id_conflict`. A verificação é feita na tabela do recurso; uma corrida entre duas requisições iguais termina na segunda lendo o registro da primeira.
**Consequências:** o app gera os ids e pode criar offline; não há tabela de chaves de idempotência.

## D41 — Sincronização incremental
**Status:** aceita · 2026-11
**Contexto:** o app precisa saber o que mudou e o que foi excluído desde a última sincronização.
**Decisão:** listas paginadas aceitam `updated_since` (incluem arquivados e ordenam por `updated_at`); `GET /api/v1/sync/deletions` devolve as exclusões e o `server_time`. Um gatilho do PostgreSQL em cada tabela de módulo grava a exclusão em `sync_deletions` (inclusive as em cascata e as feitas em lote) e ignora as causadas pela exclusão do próprio usuário. Registros guardados por 180 dias; `since` mais antigo responde `410`.
**Consequências:** cada módulo novo cria o gatilho das suas tabelas na própria migration (`docs/novo-modulo.md`). Valores derivados não alteram `updated_at`.

## D42 — Changelog e app Android
**Status:** aceita · 2026-11
**Contexto:** a Fase 5 previa um changelog próprio da API e o repositório do app.
**Decisão:** as mudanças da API entram no `CHANGELOG` do projeto, gerado do GitHub (`make changelog`), sem arquivo separado. O repositório `prumo-android` começa em outra sessão.
**Consequências:** mudanças de contrato precisam de issue ou pull request descritivos para aparecer no changelog.

## D43 — Servidor e app no mesmo fluxo de trabalho
**Status:** aceita · 2026-11
**Contexto:** o app Android (`prumo-android`) consome esta API e revela lacunas dela enquanto é construído. O `CLAUDE.md` pedia commits locais, e o mantenedor prefere revisar e commitar à mão nos dois repositórios.
**Decisão:** seção "Servidor e app juntos" no `CLAUDE.md` dos dois repositórios: a mudança que um lado precisa é feita no outro na mesma tarefa, seguindo o `CLAUDE.md` de lá; ninguém faz commit, stage nem push (exceto num branch de trabalho, quando o mantenedor pede numa sessão na nuvem); toda mudança é descrita em `commit-message.md` na raiz do repositório, ignorado pelo git.
**Consequências:** substitui a regra de "commits locais pequenos". O histórico passa pelas mãos do mantenedor, e cada lado de uma mudança conjunta cita o outro na mensagem.

## D44 — O health identifica o servidor
**Status:** aceita · 2026-11
**Contexto:** no primeiro acesso, o app testa o endereço digitado e precisa distinguir "não é um servidor Prumo" de "servidor fora do ar" (lacuna A5 do design do app). Inferir pelo formato da resposta (`status`, `database`, `version`) aceitaria qualquer serviço com um JSON parecido.
**Decisão:** `GET /api/health` ganha `service`, sempre `"prumo"`, também na resposta `503`. Mudança aditiva, sem migration.
**Consequências:** o app trata como "não é um servidor Prumo" uma resposta com outro `service` ou sem o formato do health. Nenhuma versão foi publicada sem o campo, mas o app ainda aceita uma resposta sem `service` e com os outros três campos (servidores de desenvolvimento anteriores a esta mudança).

## D45 — Mais ícones de categoria, os mesmos na web e no app
**Status:** aceita · 2026-11
**Contexto:** o seletor de ícone das categorias oferecia 14 ícones na web e 19 no app, pouco para separar as despesas de uma casa (mercado, aluguel, energia, farmácia, academia…). O ícone é um nome livre (`[a-z0-9-]`, D33), então ampliar não muda a API.
**Decisão:** 80 ícones de categoria em oito grupos (casa, alimentação, transporte, saúde e cuidado, lazer, pessoal e família, trabalho e estudo, dinheiro e contas), com nomes do Lucide da versão instalada (`shopping-cart`, `key`, `pill`, `square-parking`…). A web lista todos em `CATEGORY_ICONS`, na ordem dos grupos, e mapeia cada nome para um nome semântico de `src/ui/icons.ts`; o app Android mostra os mesmos nomes por grupo, com busca, e desenha cada um com o Material Symbol mais próximo (D23 do app). Os ícones de conta continuam os cinco de antes. O ícone `ticket` (Lazer) continua o mesmo nome.
**Consequências:** um nome novo precisa entrar nos dois clientes (aqui: `icons.ts`, `ICONS`, `CATEGORY_ICONS` e o rótulo em `locales/pt-BR.json`); um cliente que não o conhece mostra o ícone genérico, como antes.

---

## Modelo

```
## Dxx — Título
**Status:** proposta | aceita | substituída por Dyy · AAAA-MM
**Contexto:** …
**Decisão:** …
**Consequências:** …
```
