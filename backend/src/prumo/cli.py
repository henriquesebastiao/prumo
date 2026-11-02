"""Command line: `prumo users create`, `prumo users set-password`, `prumo openapi`.

There is no public sign-up; users are created here (S1).
"""

import argparse
import getpass
import sys
from collections.abc import Sequence
from pathlib import Path

from prumo.core.db import get_sessionmaker
from prumo.core.errors import DomainError


def _read_password(from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.readline().rstrip("\n")
    while True:
        password = getpass.getpass("Senha: ")
        if password == getpass.getpass("Repita a senha: "):
            return password
        print("As senhas não conferem. Tente de novo.", file=sys.stderr)


def _prompt(label: str, value: str | None) -> str:
    if value:
        return value
    while not (value := input(f"{label}: ").strip()):
        pass
    return value


def _users_create(args: argparse.Namespace) -> int:
    from prumo.main import bootstrap
    from prumo.system.users.service import create_user

    bootstrap()
    username = _prompt("Usuário", args.username)
    display_name = _prompt("Nome de exibição", args.name)
    password = _read_password(args.password_stdin)
    with get_sessionmaker()() as session:
        user = create_user(
            session,
            username=username,
            display_name=display_name,
            password=password,
            is_admin=args.admin,
        )
    role = "administrador" if user.is_admin else "usuário"
    print(f"Criado {role} '{user.username}'.")
    return 0


def _users_set_password(args: argparse.Namespace) -> int:
    from prumo.main import bootstrap
    from prumo.system.users.service import get_by_username, set_password

    bootstrap()
    with get_sessionmaker()() as session:
        user = get_by_username(session, args.username)
        if user is None:
            print(f"Usuário '{args.username}' não encontrado.", file=sys.stderr)
            return 1
        set_password(session, user, _read_password(args.password_stdin))
    print(f"Senha de '{user.username}' alterada.")
    return 0


def _openapi(args: argparse.Namespace) -> int:
    from prumo.openapi import build_schema, render_schema

    content = render_schema(build_schema())
    if args.output == "-":
        sys.stdout.write(content)
    else:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"OpenAPI escrito em {path}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prumo", description="Administração do Prumo.")
    commands = parser.add_subparsers(dest="command", required=True)

    users = commands.add_parser("users", help="Gerenciar usuários.")
    user_commands = users.add_subparsers(dest="users_command", required=True)

    create = user_commands.add_parser("create", help="Criar um usuário.")
    create.add_argument("--username", help="Nome de usuário (pedido se omitido).")
    create.add_argument("--name", help="Nome de exibição (pedido se omitido).")
    create.add_argument("--admin", action="store_true", help="Criar como administrador.")
    create.add_argument(
        "--password-stdin", action="store_true", help="Ler a senha da entrada padrão."
    )
    create.set_defaults(handler=_users_create)

    set_password = user_commands.add_parser("set-password", help="Redefinir a senha.")
    set_password.add_argument("username")
    set_password.add_argument(
        "--password-stdin", action="store_true", help="Ler a senha da entrada padrão."
    )
    set_password.set_defaults(handler=_users_set_password)

    openapi = commands.add_parser("openapi", help="Exportar o contrato OpenAPI.")
    openapi.add_argument("output", nargs="?", default="-", help="Arquivo de saída (- = stdout).")
    openapi.set_defaults(handler=_openapi)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        code: int = args.handler(args)
    except DomainError as error:
        print(f"Erro: {error.message} ({error.code})", file=sys.stderr)
        return 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
