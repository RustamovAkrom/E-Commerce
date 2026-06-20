#!/usr/bin/env python
"""Project management CLI.

A single entry point for every routine task: migrations, running the server,
tests, linting, type-checking and a few utilities. Run it with no arguments
for an interactive numbered menu (no need to remember commands), or pass a
command name directly.

Examples
--------
    uv run python manage.py              # interactive menu
    uv run python manage.py migrate      # apply migrations
    uv run python manage.py makemigration -m "add coupons"
    uv run python manage.py test
    uv run python manage.py verify       # lint + types + import + tests
    uv run python manage.py createsuperuser -e admin@test.uz -f password123

This script only orchestrates ``uv``/``alembic``/``pytest``/``ruff``/``mypy``/
``uvicorn`` subprocesses — it contains no business logic itself.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

# Enable ANSI colours on Windows terminals (no-op elsewhere).
if os.name == "nt":
    os.system("")


class C:
    """Minimal ANSI colour helpers (disabled when output is not a TTY)."""

    @staticmethod
    def _wrap(code: str, text: str) -> str:
        if not sys.stdout.isatty():
            return text
        return f"\033[{code}m{text}\033[0m"

    @classmethod
    def bold(cls, t: str) -> str:
        return cls._wrap("1", t)

    @classmethod
    def green(cls, t: str) -> str:
        return cls._wrap("32", t)

    @classmethod
    def red(cls, t: str) -> str:
        return cls._wrap("31", t)

    @classmethod
    def yellow(cls, t: str) -> str:
        return cls._wrap("33", t)

    @classmethod
    def cyan(cls, t: str) -> str:
        return cls._wrap("36", t)

    @classmethod
    def dim(cls, t: str) -> str:
        return cls._wrap("2", t)


def run(*args: str, env: dict[str, str] | None = None) -> int:
    """Run a subprocess in the backend directory; return its exit code."""
    printable = " ".join(args)
    print(C.dim(f"$ {printable}"))
    full_env = {**os.environ, **(env or {})}
    try:
        completed = subprocess.run(list(args), cwd=BACKEND_DIR, env=full_env)
        return completed.returncode
    except FileNotFoundError:
        print(C.red(f"Command not found: {args[0]}"))
        return 127
    except KeyboardInterrupt:
        print(C.yellow("\nInterrupted."))
        return 130


# --- Command implementations -----------------------------------------------
def cmd_run(extra: list[str]) -> int:
    """Start the API server with autoreload (uvicorn)."""
    host = "0.0.0.0"  # noqa: S104  -- dev server, bind all interfaces intentionally
    port = "8000"
    return run(
        "uv", "run", "uvicorn", "src.main:app",
        "--reload", "--host", host, "--port", port, *extra,
    )


def cmd_test(extra: list[str]) -> int:
    """Run the test suite (pytest)."""
    return run("uv", "run", "pytest", *(extra or ["-v", "--tb=short"]))


def cmd_lint(extra: list[str]) -> int:
    """Lint and auto-fix with ruff."""
    return run("uv", "run", "ruff", "check", ".", "--fix", *extra)


def cmd_format(extra: list[str]) -> int:
    """Auto-format the codebase with ruff."""
    return run("uv", "run", "ruff", "format", ".", *extra)


def cmd_typecheck(extra: list[str]) -> int:
    """Static type check with mypy."""
    return run("uv", "run", "mypy", "src/", *extra)


def cmd_check(extra: list[str]) -> int:
    """Import the app to confirm it wires up cleanly."""
    return run(
        "uv", "run", "python", "-c",
        "from src.main import app; print('Backend import: OK')",
    )


def cmd_verify(extra: list[str]) -> int:
    """Run the full quality gate: lint -> types -> import -> tests."""
    steps: list[tuple[str, Callable[[list[str]], int]]] = [
        ("Lint (ruff)", cmd_lint),
        ("Type check (mypy)", cmd_typecheck),
        ("Import check", cmd_check),
        ("Tests (pytest)", cmd_test),
    ]
    failed: list[str] = []
    for label, fn in steps:
        print(C.bold(C.cyan(f"\n=== {label} ===")))
        if fn([]) != 0:
            failed.append(label)
    print()
    if failed:
        print(C.red(f"FAILED: {', '.join(failed)}"))
        return 1
    print(C.green("All checks passed."))
    return 0


def cmd_migrate(extra: list[str]) -> int:
    """Apply all pending migrations (alembic upgrade head)."""
    return run("uv", "run", "alembic", "upgrade", "head", *extra)


def cmd_makemigration(extra: list[str]) -> int:
    """Autogenerate a new migration. Prompts for a message if none given."""
    message = _extract_message(extra)
    if not message:
        message = _prompt("Migration message")
    if not message:
        print(C.red("A migration message is required."))
        return 1
    return run(
        "uv", "run", "alembic", "revision", "--autogenerate", "-m", message
    )


def cmd_rollback(extra: list[str]) -> int:
    """Roll back the most recent migration (downgrade -1)."""
    return run("uv", "run", "alembic", "downgrade", "-1", *extra)


def cmd_db_current(extra: list[str]) -> int:
    """Show the current migration revision."""
    return run("uv", "run", "alembic", "current", *extra)


def cmd_db_history(extra: list[str]) -> int:
    """Show the migration history."""
    return run("uv", "run", "alembic", "history", "--indicate-current", *extra)


def cmd_db_reset(extra: list[str]) -> int:
    """Drop all migrations then re-apply (downgrade base -> upgrade head)."""
    if not _confirm(
        "This will downgrade to base (drops all tables) then rebuild. Continue?"
    ):
        print(C.yellow("Cancelled."))
        return 0
    code = run("uv", "run", "alembic", "downgrade", "base")
    if code != 0:
        return code
    return run("uv", "run", "alembic", "upgrade", "head")


def cmd_install(extra: list[str]) -> int:
    """Install/sync dependencies including the dev extras."""
    return run("uv", "sync", "--extra", "dev", *extra)


def cmd_routes(extra: list[str]) -> int:
    """List all registered API routes."""
    script = (
        "from src.main import app\n"
        "rows = []\n"
        "for r in app.routes:\n"
        "    methods = ','.join(sorted(getattr(r, 'methods', []) or []))\n"
        "    rows.append((methods, getattr(r, 'path', '')))\n"
        "for methods, path in sorted(rows, key=lambda x: x[1]):\n"
        "    print(f'{methods:<22} {path}')\n"
        "print(f'\\n{len(rows)} routes')\n"
    )
    return run("uv", "run", "python", "-c", script)


def cmd_secret(extra: list[str]) -> int:
    """Generate a strong SECRET_KEY value."""
    return run(
        "uv", "run", "python", "-c",
        "import secrets; print(secrets.token_urlsafe(48))",
    )


def cmd_shell(extra: list[str]) -> int:
    """Open a Python REPL with the project environment."""
    return run("uv", "run", "python")


def cmd_setup_test_db(extra: list[str]) -> int:
    """Create the test database (ecommerce_test) if it doesn't exist."""
    import asyncio
    import asyncpg

    default_db_url = "postgresql://postgres:postgres@localhost:5432/postgres"

    async def _setup() -> int:
        conn = await asyncpg.connect(default_db_url)
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", "ecommerce_test"
            )
            if not exists:
                await conn.execute("CREATE DATABASE ecommerce_test")
                print(C.green("Test database created."))
            else:
                print(C.yellow("Test database already exists."))
        finally:
            await conn.close()
        return 0

    return asyncio.run(_setup())


# --- Superadmin -------------------------------------------------------------
async def _create_superadmin_cmd(args: list[str]) -> int:
    """Create or reset a SUPERADMIN user (Django-style createsuperuser)."""
    from sqlalchemy import select
    from src.core.database import async_session_maker
    from src.core.security import hash_password
    from src.modules.users.models import User

    # Parse CLI flags (--email, --password, --name, --force-password)
    flags: dict[str, str] = {}
    i = 0
    while i < len(args):
        if args[i] in {"--email", "-e"} and i + 1 < len(args):
            flags["email"] = args[i + 1]
            i += 2
        elif args[i] in {"--password", "-p"} and i + 1 < len(args):
            flags["password"] = args[i + 1]
            i += 2
        elif args[i] in {"--name", "-n"} and i + 1 < len(args):
            flags["name"] = args[i + 1]
            i += 2
        elif args[i] in {"--force-password", "-f"} and i + 1 < len(args):
            flags["force_password"] = args[i + 1]
            i += 2
        else:
            i += 1

    from src.config import settings

    # Interactive prompts for missing fields
    if "email" not in flags:
        flags["email"] = _prompt("Email (superadmin)") or settings.ADMIN_EMAIL
    if "password" not in flags and "force_password" not in flags:
        pw1 = _prompt("Password")
        if not pw1:
            print(C.red("Password is required."))
            return 1
        pw2 = _prompt("Password (again)")
        if pw1 != pw2:
            print(C.red("Passwords do not match."))
            return 1
        flags["password"] = pw1
    elif "force_password" in flags:
        flags["password"] = flags["force_password"]
    if "name" not in flags:
        flags["name"] = _prompt("Full name (optional, Enter = skip)") or ""

    async with async_session_maker() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.email == flags["email"])
        )
        user = result.scalar_one_or_none()

        if user:
            # Reset password for existing user
            print(
                C.yellow(
                    f"User {flags['email']} already exists. "
                    f"Resetting password and ensuring role=SUPERADMIN."
                )
            )
            user.hashed_password = hash_password(flags["password"])
            user.role = "SUPERADMIN"
            user.is_active = True
            user.is_verified = True
            if flags["name"]:
                user.full_name = flags["name"]
        else:
            # Create new user
            user = User(
                email=flags["email"],
                hashed_password=hash_password(flags["password"]),
                full_name=flags["name"] or flags["email"].split("@")[0],
                role="SUPERADMIN",
                is_active=True,
                is_verified=True,
            )
            session.add(user)

        try:
            await session.flush()
        except Exception as exc:
            await session.rollback()
            print(C.red(f"Failed: {exc}"))
            return 1

    print(
        C.green(
            f"Superadmin {'updated' if user.id else 'created'}: "
            f"{flags['email']}"
        )
    )
    return 0


def cmd_create_superadmin(extra: list[str]) -> int:
    """Create or reset a SUPERADMIN user (like Django's createsuperuser)."""
    return asyncio.run(_create_superadmin_cmd(extra))


# --- Command registry -------------------------------------------------------
@dataclass(frozen=True)
class Command:
    name: str
    help: str
    func: Callable[[list[str]], int]
    aliases: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Group:
    title: str
    commands: list[Command]


GROUPS: list[Group] = [
    Group(
        "Server",
        [
            Command("run", "Start the API server (autoreload)", cmd_run, ("serve",)),
        ],
    ),
    Group(
        "Database",
        [
            Command("migrate", "Apply pending migrations (upgrade head)", cmd_migrate),
            Command(
                "makemigration",
                "Autogenerate a new migration (-m 'msg')",
                cmd_makemigration,
                ("revision",),
            ),
            Command("rollback", "Roll back the last migration", cmd_rollback),
            Command("db-current", "Show current revision", cmd_db_current),
            Command("db-history", "Show migration history", cmd_db_history),
            Command("db-reset", "Downgrade to base then rebuild", cmd_db_reset),
            Command("setup-test-db", "Create test database (ecommerce_test)", cmd_setup_test_db),
        ],
    ),
    Group(
        "Users",
        [
            Command(
                "createsuperuser",
                "Create/reset a SUPERADMIN user (Django-style)",
                cmd_create_superadmin,
                ("create-superuser", "superadmin"),
            ),
        ],
    ),
    Group(
        "Quality",
        [
            Command("test", "Run the test suite", cmd_test),
            Command("lint", "Lint + autofix (ruff)", cmd_lint),
            Command("format", "Format code (ruff)", cmd_format),
            Command("typecheck", "Static type check (mypy)", cmd_typecheck),
            Command("check", "Import check (app wires up)", cmd_check),
            Command("verify", "Full gate: lint+types+import+tests", cmd_verify),
        ],
    ),
    Group(
        "Utilities",
        [
            Command("install", "Sync dependencies (+dev extras)", cmd_install),
            Command("routes", "List all API routes", cmd_routes),
            Command("secret", "Generate a SECRET_KEY", cmd_secret),
            Command("shell", "Open a Python REPL", cmd_shell),
        ],
    ),
]


def _all_commands() -> dict[str, Command]:
    table: dict[str, Command] = {}
    for group in GROUPS:
        for command in group.commands:
            table[command.name] = command
            for alias in command.aliases:
                table[alias] = command
    return table


COMMANDS = _all_commands()


# --- Interactive prompts ----------------------------------------------------
def _prompt(label: str) -> str:
    try:
        return input(C.cyan(f"{label}: ")).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def _confirm(question: str) -> bool:
    answer = _prompt(f"{question} [y/N]").lower()
    return answer in {"y", "yes"}


def _extract_message(extra: list[str]) -> str | None:
    """Pull the value following -m/--message from passthrough args."""
    for flag in ("-m", "--message"):
        if flag in extra:
            idx = extra.index(flag)
            if idx + 1 < len(extra):
                return extra[idx + 1]
    return None


# --- Menu -------------------------------------------------------------------
def print_help() -> None:
    print(C.bold("\nProject management CLI"))
    print(C.dim("Usage: uv run python manage.py [command] [args...]"))
    print(C.dim("Run with no command for an interactive menu.\n"))
    for group in GROUPS:
        print(C.bold(C.yellow(group.title)))
        for command in group.commands:
            print(f"  {C.green(command.name):<28} {command.help}")
        print()


def interactive_menu() -> int:
    """Numbered menu loop — pick a command without typing its name."""
    indexed: list[Command] = []
    while True:
        indexed.clear()
        print(C.bold(C.cyan("\n=== E-COMMERCE - Management Console ===")))
        counter = 1
        for group in GROUPS:
            print(C.bold(C.yellow(f"\n  {group.title}")))
            for command in group.commands:
                indexed.append(command)
                print(
                    f"   {C.green(f'{counter:>2}')}  "
                    f"{command.name:<16} {C.dim(command.help)}"
                )
                counter += 1
        print(C.dim("\n    q  quit"))

        choice = _prompt("\nSelect").lower()
        if choice in {"q", "quit", "exit", ""}:
            print(C.dim("Bye."))
            return 0

        command: Command | None = None
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(indexed):
                command = indexed[num - 1]
        else:
            command = COMMANDS.get(choice)

        if command is None:
            print(C.red("Invalid choice, try again."))
            continue

        print(C.bold(C.cyan(f"\n> {command.name}")))
        code = command.func([])
        status = C.green("[OK] done") if code == 0 else C.red(f"[FAILED] exit {code}")
        print(status)


def main(argv: list[str]) -> int:
    if not argv:
        return interactive_menu()

    head, *extra = argv
    if head in {"-h", "--help", "help"}:
        print_help()
        return 0

    command = COMMANDS.get(head)
    if command is None:
        print(C.red(f"Unknown command: {head}"))
        print_help()
        return 2
    return command.func(extra)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
