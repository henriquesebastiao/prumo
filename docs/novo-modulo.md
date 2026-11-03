# Como criar um módulo

Exemplo usado neste guia: um módulo hipotético de hábitos, com id `habits`.

## 1. Defina antes de codar

- **id**: em inglês, curto, estável (vira prefixo de rota, de tabela e chave de preferência). Não mude depois de publicado.
- **Nome exibido**: em pt-BR, no i18n.
- **Entidades e regras**: nova seção em `docs/dominio.md`, com regras numeradas (H1, H2…).
- **Rotas**: nova seção em `docs/api.md`.
- **Plano**: nova fase ou item em `ROADMAP.md`.

## 2. Backend

```
backend/src/prumo/modules/habits/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
├── router.py
└── summary.py
```

```python
# models.py
class Habit(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "habits_habits"          # sempre com o prefixo do módulo

    name: Mapped[str] = mapped_column(String(120))
```

```python
# service.py
def list_habits(session: Session, user: User, page: PageParams) -> Page[Habit]:
    stmt = select(Habit).where(Habit.user_id == user.id)   # sempre filtrado pelo usuário
    return paginate(session, stmt, page)

def get_habit(session: Session, user: User, habit_id: UUID) -> Habit:
    habit = session.scalar(select(Habit).where(Habit.id == habit_id, Habit.user_id == user.id))
    if habit is None:
        raise NotFoundError()                # vira 404 com o formato padrão
    return habit
```

```python
# router.py
router = APIRouter()

@router.get("/habits", response_model=Page[HabitRead])
def list_habits(session: SessionDep, user: CurrentUser, page: PageDep) -> Page[Habit]:
    return service.list_habits(session, user, page)
```

```python
# summary.py (opcional): o tipo de retorno define o schema do resumo no OpenAPI
class HabitsSummary(ModuleSummary):          # from prumo.core.modules import ModuleSummary
    module: Literal["habits"] = "habits"     # discriminador da união do dashboard
    done_today: int

def build_summary(session: Session, user: User) -> HabitsSummary:
    ...
```

Imports usados acima: `SessionDep` de `prumo.core.deps`, `CurrentUser` de `prumo.system.auth.deps`, `PageDep`, `PageParams`, `Page` e `paginate` de `prumo.core.pagination`, `NotFoundError` de `prumo.core.errors`, `User` de `prumo.system.users.models`.

```python
# __init__.py
module = PrumoModule(
    id="habits",
    version="0.1.0",
    router=router,
    summary=build_summary,     # opcional: bloco no Início
)
```

Depois:

1. Adicione `habits.module` a `INSTALLED_MODULES` em `modules/__init__.py`.
2. Adicione o módulo ao contrato do `import-linter`.
3. `make migration m="add habits module"` e revise o arquivo.
4. Testes em `tests/modules/habits/`: regras de serviço, endpoints, e acesso de outro usuário retornando 404.
5. Se o módulo tiver resumo no Início, basta o `summary` com o tipo de retorno anotado: a união discriminada do dashboard é montada a partir dos módulos instalados. Para aparecer em "Vem aí" e "Atividade recente", forneça `upcoming` e `activity` no `PrumoModule` e documente os `kind` e os campos de `data` em `docs/api.md`. Para entrar na exportação dos dados do usuário (D38), forneça `export`: uma função que devolve `ModuleExport` com as tabelas (`table_rows` de `core/export.py` faz o trabalho) e, se houver, os arquivos enviados.
6. `make openapi`.

## 3. Frontend

```
frontend/src/modules/habits/
├── index.ts
├── routes.ts
├── api.ts
├── pages/
├── forms/
├── widgets/HabitsWidget.vue
└── locales/pt-BR.json
```

```ts
// index.ts
export default defineModule({
  id: 'habits',
  icon: 'repeat',
  nav: { labelKey: 'habits.nav', route: 'habits.home' },
  routes,
  dashboardWidget: () => import('./widgets/HabitsWidget.vue'),
  descriptionKey: 'habits.description',
  quickActions: [],             // { id, labelKey, icon, shortcut?, pinned?, component }
  messages: { 'pt-BR': () => import('./locales/pt-BR.json') },
})
```

Depois:

1. Adicione o módulo a `src/modules/index.ts`.
2. Crie os tokens `--color-module-habits`, `-container`, `-on-container`, `-soft` e `-softer` em `src/design/themes/light.css` e `dark.css`, e o bloco `[data-tone='habits']` em `src/design/tones.css` (veja "Cores por módulo" em `docs/frontend.md`).
3. Telas só com componentes de `src/ui/`. Se faltar um componente genérico, crie em `src/ui/` e coloque na vitrine `/dev/ui`; se for específico do módulo, crie em `modules/habits/components/` compondo componentes de `src/ui/`.
4. Todos os textos em `locales/pt-BR.json`; as traduções dos códigos de erro `habits.*` vão em `src/app/locales/pt-BR.json`, em `errors.habits`.
5. Se o backend publica itens de "Vem aí" ou "Atividade recente", implemente `describeUpcoming` e `describeActivity` na definição do módulo.
6. Dados das telas do design no `backend/scripts/e2e_server.py` e capturas em `frontend/e2e/`, para comparar com o design (`make screenshots`).

## 4. Feche

- [ ] `make check` verde
- [ ] `docs/dominio.md`, `docs/api.md` e `ROADMAP.md` atualizados
- [ ] Módulo aparece em `GET /api/v1/modules`, na navegação e no Início, e some quando desativado nas Configurações
