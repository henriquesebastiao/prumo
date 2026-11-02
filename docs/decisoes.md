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
**Status:** pendente
**Contexto:** projeto open source e self-hosted.
**Decisão:** a definir antes da versão 0.1.

---

## Modelo

```
## Dxx — Título
**Status:** proposta | aceita | substituída por Dyy · AAAA-MM
**Contexto:** …
**Decisão:** …
**Consequências:** …
```
