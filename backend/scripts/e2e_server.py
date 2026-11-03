"""API for the Playwright screenshots: a throwaway database seeded with the data of the design
boards, served with the clock frozen at the moment of the boards (Tue 17 Nov 2026, 14:30 in
São Paulo).

Run from backend/: `uv run python scripts/e2e_server.py` (used by frontend/playwright.config.ts).
Database: PRUMO_E2E_DATABASE_URL, default prumo_e2e on the test container (port 5433).
"""

import os
import shutil
from datetime import UTC, date, datetime, time
from pathlib import Path

import psycopg
import time_machine
import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

ADMIN_URL = os.environ.get(
    "PRUMO_E2E_ADMIN_URL", "postgresql://prumo:prumo@localhost:5433/prumo_test"
)
DATABASE_URL = os.environ.get(
    "PRUMO_E2E_DATABASE_URL", "postgresql+psycopg://prumo:prumo@localhost:5433/prumo_e2e"
)
PORT = int(os.environ.get("PRUMO_E2E_PORT", "8001"))
NOW = "2026-11-17T17:30:00Z"

UPLOADS = Path(__file__).resolve().parents[2] / "data" / "e2e-uploads"

os.environ["PRUMO_DATABASE_URL"] = DATABASE_URL
os.environ["PRUMO_COOKIE_SECURE"] = "false"
os.environ["PRUMO_UPLOADS_DIR"] = str(UPLOADS)


def at(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def reset_database() -> None:
    shutil.rmtree(UPLOADS, ignore_errors=True)
    with psycopg.connect(ADMIN_URL, autocommit=True) as connection:
        connection.execute("DROP DATABASE IF EXISTS prumo_e2e WITH (FORCE)")
        connection.execute("CREATE DATABASE prumo_e2e")
    config = Config("alembic.ini")
    config.attributes["configure_logger"] = False
    engine = create_engine(DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    engine.dispose()


def seed() -> None:
    from prumo.main import bootstrap
    from prumo.modules.garage import service
    from prumo.modules.garage.models import FuelType, MaintenanceKind, VehicleKind
    from prumo.modules.garage.schemas import (
        FuelingCreate,
        MaintenanceCreate,
        MaintenanceItemIn,
        OdometerReadingCreate,
        VehicleCreate,
    )
    from prumo.system.users.service import create_user

    bootstrap()
    engine = create_engine(DATABASE_URL)
    with Session(engine, expire_on_commit=False) as session:
        with time_machine.travel(at("2025-11-19T12:00:00")):
            user = create_user(
                session,
                username="henrique",
                display_name="Henrique Sebastião",
                password="prumo-demo-01",
                is_admin=True,
            )
            cg = service.create_vehicle(
                session,
                user,
                VehicleCreate(
                    kind=VehicleKind.MOTORCYCLE,
                    name="Honda CG 160 Fan",
                    brand="Honda",
                    model="CG 160 Fan",
                    year=2023,
                    fuel_type=FuelType.GASOLINE,
                    current_km=11000,
                    oil_interval_km=1000,
                    oil_interval_months=3,
                ),
            )
        with time_machine.travel(at("2025-11-20T12:00:00")):
            strada = service.create_vehicle(
                session,
                user,
                VehicleCreate(
                    kind=VehicleKind.CAR,
                    name="Fiat Strada Freedom",
                    brand="Fiat",
                    model="Strada Freedom",
                    year=2021,
                    fuel_type=FuelType.GASOLINE,
                    current_km=46000,
                    oil_interval_km=10000,
                    oil_interval_months=12,
                ),
            )

        def maintenance(vehicle, when, km, items, labor, notes=None) -> None:  # type: ignore[no-untyped-def]
            service.create_maintenance(
                session,
                user,
                vehicle,
                MaintenanceCreate(
                    performed_at=at(when),
                    km=km,
                    workshop_name="Moto Peças Rocha",
                    labor_cost_cents=labor,
                    notes=notes,
                    items=[MaintenanceItemIn(description=d, unit_price_cents=p) for d, p in items],
                ),
            )

        def oil(vehicle, when, km, oil_type, **next_values) -> None:  # type: ignore[no-untyped-def]
            service.create_maintenance(
                session,
                user,
                vehicle,
                MaintenanceCreate(
                    kind=MaintenanceKind.OIL_CHANGE,
                    performed_at=at(when),
                    km=km,
                    oil_type=oil_type,
                    labor_cost_cents=1500,
                    items=[
                        MaintenanceItemIn(description="Óleo " + oil_type, unit_price_cents=3890)
                    ],
                    **next_values,
                ),
            )

        def fuel(vehicle, when, km, ml, cents, full=True) -> None:  # type: ignore[no-untyped-def]
            service.create_fueling(
                session,
                user,
                vehicle,
                FuelingCreate(
                    fueled_at=at(when), km=km, volume_ml=ml, total_cents=cents, full_tank=full
                ),
            )

        oil(
            strada,
            "2025-12-05T14:00:00",
            46900,
            "5W-30 sintético",
            next_oil_change_km=56900,
            next_oil_change_on=date(2026, 12, 5),
        )
        maintenance(
            cg,
            "2026-05-22T13:30:00",
            13050,
            [("Cabo de embreagem", 2800), ("Lâmpada do farol", 1890)],
            3000,
        )
        oil(cg, "2026-06-20T13:00:00", 13900, "4T 10W-30 sintético")
        maintenance(
            cg,
            "2026-07-14T13:30:00",
            14620,
            [("Pneu traseiro 90/90-18", 21900), ("Câmara de ar", 3200)],
            2500,
        )
        maintenance(
            cg,
            "2026-09-03T13:30:00",
            16180,
            [
                ("Kit relação (coroa, pinhão e corrente)", 18990),
                ("Pastilha de freio dianteira", 3450),
            ],
            6000,
            "Corrente estava no limite de esticamento. O mecânico recomendou olhar a lona do freio "
            "traseiro na próxima visita.",
        )
        oil(cg, "2026-09-12T13:00:00", 16640, "4T 20W-50 semissintético")
        fuel(cg, "2026-09-27T12:00:00", 16900, 7000, 4410)
        fuel(cg, "2026-10-07T12:00:00", 17200, 7280, 4600)
        fuel(cg, "2026-10-17T12:00:00", 17500, 7480, 4730)
        oil(cg, "2026-10-21T13:00:00", 17640, "4T 20W-50 semissintético")
        fuel(cg, "2026-10-27T12:00:00", 17800, 7520, 4770)
        fuel(cg, "2026-11-06T12:00:00", 18110, 7640, 4850)
        fuel(strada, "2026-10-28T20:00:00", 51900, 30000, 18900)
        fuel(strada, "2026-11-13T21:00:00", 52300, 28400, 18034)
        fuel(cg, "2026-11-16T21:10:00", 18400, 7300, 4636)
        with time_machine.travel(at("2026-11-15T22:20:00")):
            service.add_manual_reading(session, user, strada, OdometerReadingCreate(km=52300))
        with time_machine.travel(at("2026-11-17T10:42:00")):
            service.add_manual_reading(session, user, cg, OdometerReadingCreate(km=18420))
        with time_machine.travel(at("2026-11-17T17:20:00")):
            seed_finance(session, user)
        seed_reading(session, user)
        # Empty account for the end-to-end flows (e2e/flows.spec.ts), apart from the boards.
        create_user(
            session, username="teste", display_name="Teste Fluxos", password="prumo-teste-01"
        )
    engine.dispose()


def seed_reading(session: Session, user: object) -> None:
    """The Livros boards: "Código Limpo" at page 212 of 425 since 26/10 (62, 71 and 79 pages per
    week, about 10 a day, ending around 08/12), "Dom Casmurro" read and "O Hobbit" to read."""
    from prumo.modules.reading import service as reading
    from prumo.modules.reading.models import BookStatus
    from prumo.modules.reading.schemas import BookCreate, NoteCreate
    from prumo.system.users.models import User

    assert isinstance(user, User)

    def local(value: str) -> datetime:
        return datetime.fromisoformat(f"{value}-03:00")

    with time_machine.travel(local("2026-09-25T20:00:00")):
        casmurro = reading.create_book(
            session,
            user,
            BookCreate(
                title="Dom Casmurro",
                author="Machado de Assis",
                total_pages=256,
                status=BookStatus.READ,
                owned=True,
                started_on=date(2026, 9, 25),
                finished_on=date(2026, 10, 18),
            ),
        )
    for day, content in (
        ("2026-09-27", "Bentinho conta a história já velho: tudo passa pelo filtro da memória."),
        ("2026-10-02", "Olhos de cigana oblíqua e dissimulada."),
        ("2026-10-09", "O capítulo dos olhos de ressaca."),
        ("2026-10-18", "O narrador não é confiável; a dúvida fica com o leitor."),
    ):
        with time_machine.travel(local(f"{day}T21:00:00")):
            reading.create_note(session, user, casmurro, NoteCreate(content=content))

    with time_machine.travel(local("2026-10-26T20:30:00")):
        clean = reading.create_book(
            session,
            user,
            BookCreate(
                title="Código Limpo", author="Robert C. Martin", total_pages=425, owned=True
            ),
        )
    for moment, page in (
        ("2026-10-26T21:00:00", 20),
        ("2026-10-28T22:00:00", 41),
        ("2026-10-31T20:00:00", 62),
        ("2026-11-02T22:00:00", 66),
        ("2026-11-05T21:00:00", 98),
        ("2026-11-08T20:00:00", 133),
        ("2026-11-10T22:00:00", 176),
        ("2026-11-13T21:00:00", 198),
        ("2026-11-15T22:05:00", 212),
    ):
        with time_machine.travel(local(moment)):
            reading.add_progress(session, user, clean, page)
    notes: tuple[tuple[str, int | None, str], ...] = (
        (
            "2026-10-27T22:00:00",
            None,
            "Ir juntando exemplos de nomes ruins que encontro no código do dia a dia.",
        ),
        (
            "2026-11-02T22:10:00",
            98,
            "Funções pequenas, com um só nível de abstração. Testar isso no próximo refactor.",
        ),
        (
            "2026-11-10T22:10:00",
            176,
            "Objetos escondem dados e mostram comportamento; estruturas de dados fazem o "
            "contrário. Bom critério para separar models de schemas.",
        ),
        (
            "2026-11-15T22:10:00",
            212,
            "Capítulo sobre tratamento de erros: revisar como a minha API devolve falhas e "
            "trocar códigos de retorno por exceções específicas.",
        ),
    )
    for moment, note_page, content in notes:
        with time_machine.travel(local(moment)):
            reading.create_note(session, user, clean, NoteCreate(content=content, page=note_page))

    with time_machine.travel(local("2026-11-02T19:00:00")):
        reading.create_book(
            session,
            user,
            BookCreate(title="O Hobbit", author="J.R.R. Tolkien", total_pages=336),
        )


def seed_finance(session: Session, user: object) -> None:
    """The Finanças boards: balances 4.812,37 · 2.156,90 · 185,00, November with R$ 5.300,00 of
    income and R$ 2.564,19 of expenses, and the open Nubank invoice of R$ 1.284,60."""
    from prumo.modules.finance import service as finance
    from prumo.modules.finance.models import AccountKind, TransactionKind
    from prumo.modules.finance.schemas import (
        AccountCreate,
        CreditCardCreate,
        InvoicePaymentCreate,
        TransactionCreate,
    )
    from prumo.system.users.models import User

    assert isinstance(user, User)
    nubank = finance.create_account(
        session, user, AccountCreate(name="Nubank", kind=AccountKind.CHECKING, color="violet")
    )
    inter = finance.create_account(
        session, user, AccountCreate(name="Inter", kind=AccountKind.CHECKING, color="orange")
    )
    wallet = finance.create_account(
        session, user, AccountCreate(name="Carteira", kind=AccountKind.CASH, color="green")
    )
    card = finance.create_card(
        session,
        user,
        CreditCardCreate(
            name="Nubank",
            limit_cents=500000,
            closing_day=3,
            due_day=10,
            payment_account_id=nubank.id,
            color="green",
        ),
    )
    categories = {
        (c.kind.value, c.name): c.id for c in finance.lookup_for(session, user).categories.values()
    }
    accounts = {"nubank": nubank.id, "inter": inter.id, "wallet": wallet.id}

    def tx(
        kind: str,
        cents: int,
        on: str,
        text: str = "",
        *,
        category: str | None = None,
        account: str | None = None,
        to: str | None = None,
        on_card: bool = False,
        at_time: str | None = None,
        installments: int | None = None,
    ) -> None:
        finance.create_transaction(
            session,
            user,
            TransactionCreate(
                kind=TransactionKind(kind),
                amount_cents=cents,
                occurred_on=date.fromisoformat(on),
                occurred_time=time.fromisoformat(at_time) if at_time else None,
                description=text,
                account_id=accounts[account] if account else None,
                destination_account_id=accounts[to] if to else None,
                credit_card_id=card.id if on_card else None,
                category_id=categories[(kind, category)] if category else None,
                installments=installments,
            ),
        )

    def spend(
        cents: int,
        on: str,
        text: str,
        category: str,
        *,
        account: str | None = None,
        on_card: bool = False,
        at_time: str | None = None,
    ) -> None:
        tx(
            "expense",
            cents,
            on,
            text,
            category=category,
            account=account,
            on_card=on_card,
            at_time=at_time,
        )

    def pay(closing: str, cents: int, on: str) -> None:
        finance.pay_invoice(
            session,
            user,
            card,
            date.fromisoformat(closing),
            InvoicePaymentCreate(
                amount_cents=cents, account_id=nubank.id, occurred_on=date.fromisoformat(on)
            ),
        )

    # June to October: the bars of the income and expenses chart.
    for month, freelance in (
        ("06", 120000),
        ("07", 160000),
        ("08", 110000),
        ("09", 180000),
        ("10", 130000),
    ):
        tx("income", 380000, f"2026-{month}-05", "Salário", category="Salário", account="nubank")
        tx(
            "income",
            freelance,
            f"2026-{month}-12",
            "Projeto",
            category="Freelance",
            account="inter",
        )
        spend(110000, f"2026-{month}-10", "Aluguel", "Moradia", account="inter")
    spend(90000, "2026-06-14", "Supermercado", "Alimentação", account="nubank")
    spend(30000, "2026-06-18", "Posto", "Combustível", account="nubank")
    spend(20000, "2026-06-21", "Show", "Lazer", account="nubank")
    spend(80000, "2026-06-25", "Dentista", "Saúde", account="nubank")
    spend(95000, "2026-07-14", "Supermercado", "Alimentação", account="nubank")
    spend(32000, "2026-07-18", "Posto", "Combustível", account="nubank")
    spend(23000, "2026-07-21", "Cinema", "Lazer", account="nubank")
    spend(100000, "2026-07-25", "Curso", "Educação", account="nubank")
    tx("expense", 130540, "2026-08-20", "Celular", category="Compras", on_card=True, installments=4)
    spend(50000, "2026-08-15", "Supermercado", "Alimentação", on_card=True)
    spend(28000, "2026-08-16", "Posto", "Combustível", on_card=True)
    spend(12000, "2026-08-17", "Cinema", "Lazer", on_card=True)
    spend(67365, "2026-08-24", "Supermercado", "Alimentação", account="nubank")
    pay("2026-09-03", 122635, "2026-09-10")
    spend(70000, "2026-09-15", "Supermercado", "Alimentação", on_card=True)
    spend(29210, "2026-09-16", "Posto", "Combustível", on_card=True)
    spend(40000, "2026-09-17", "Show", "Lazer", on_card=True)
    spend(98155, "2026-09-24", "Exames", "Saúde", account="nubank")
    pay("2026-10-03", 171845, "2026-10-09")
    spend(80583, "2026-10-15", "Supermercado", "Alimentação", on_card=True)
    spend(30000, "2026-10-16", "Posto", "Combustível", on_card=True)
    spend(50000, "2026-10-17", "Viagem curta", "Lazer", on_card=True)
    spend(36782, "2026-10-24", "Supermercado", "Alimentação", account="nubank")

    # November.
    tx("income", 380000, "2026-11-05", "Salário", category="Salário", account="nubank")
    tx("income", 150000, "2026-11-12", "Site institucional", category="Freelance", account="inter")
    tx("transfer", 20000, "2026-11-04", account="nubank", to="wallet")
    tx("transfer", 50000, "2026-11-12", account="inter", to="nubank")
    spend(110000, "2026-11-10", "Aluguel", "Moradia", account="inter")
    spend(18640, "2026-11-09", "Energia elétrica", "Moradia", on_card=True)
    spend(9990, "2026-11-05", "Internet", "Moradia", on_card=True)
    spend(12000, "2026-11-03", "Mercado", "Alimentação", account="nubank")
    spend(3824, "2026-11-03", "Hortifruti", "Alimentação", account="nubank")
    spend(2200, "2026-11-04", "Lanche", "Alimentação", account="wallet")
    spend(3050, "2026-11-07", "iFood", "Alimentação", account="nubank")
    spend(6430, "2026-11-08", "Feira", "Alimentação", account="wallet")
    spend(9260, "2026-11-11", "Restaurante", "Alimentação", on_card=True)
    spend(14431, "2026-11-15", "Padaria e açougue", "Alimentação", on_card=True)
    spend(21240, "2026-11-16", "Supermercado", "Alimentação", account="nubank", at_time="11:25")
    spend(1850, "2026-11-17", "Padaria", "Alimentação", account="wallet", at_time="08:10")
    spend(4434, "2026-11-06", "Posto · CG 160", "Combustível", on_card=True)
    spend(18034, "2026-11-13", "Posto · Strada", "Combustível", on_card=True, at_time="18:00")
    spend(4636, "2026-11-16", "Posto · CG 160", "Combustível", on_card=True, at_time="18:10")
    spend(3510, "2026-11-07", "Livraria", "Lazer", on_card=True)
    spend(2500, "2026-11-08", "Sorvete", "Lazer", on_card=True)
    spend(6400, "2026-11-14", "Cinema", "Lazer", on_card=True)
    spend(3990, "2026-11-15", "Streaming", "Lazer", on_card=True)
    pay("2026-11-03", 193218, "2026-11-10")

    # Initial balances that end on the balances of the boards.
    targets = {nubank.id: 481237, inter.id: 215690, wallet.id: 18500}
    current = finance.balances(session, user, [nubank, inter, wallet], date(2026, 11, 17))
    for account in (nubank, inter, wallet):
        account.initial_balance_cents = targets[account.id] - current[account.id]
    session.commit()


def main() -> None:
    reset_database()
    seed()
    with time_machine.travel(NOW, tick=True):
        uvicorn.run(
            "prumo.main:create_app", factory=True, host="127.0.0.1", port=PORT, log_level="warning"
        )


if __name__ == "__main__":
    main()
