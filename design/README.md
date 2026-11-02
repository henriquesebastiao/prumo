# Design

Exportações do Claude Design usadas como **referência visual**. Nada daqui é importado pelo código: os tokens e componentes vivem em `frontend/src/design/` e `frontend/src/ui/`.

**Versão ativa: `v1/`**

| Versão | Conteúdo | Status |
|---|---|---|
| `v1/` | `prumo.html` (exportação completa, 30 pranchas) e uma imagem PNG por prancha, renderizadas em 2× | ativa |

## Como usar

- As imagens são a referência para comparação por screenshot (Playwright, `make screenshots`). Elas foram renderizadas com densidade 2×: uma prancha de 1440 px de largura vira uma imagem de 2880 px.
- O `prumo.html` abre no navegador e contém o CSS original (`prumo.css`) com os tokens dos dois temas.
- Os arquivos de uma versão nunca são alterados. Um redesign entra como `v2/`, e esta tabela passa a indicar a nova versão ativa (veja "Como fazer um redesign" em `docs/frontend.md`).
