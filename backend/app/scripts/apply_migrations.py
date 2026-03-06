from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"


def _get_database_url() -> str:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    candidates = (
        "DATABASE_URL",
        "SUPABASE_DB_URL",
        "SUPABASE_DATABASE_URL",
    )
    for key in candidates:
        value = os.getenv(key)
        if value:
            return value
    raise RuntimeError(
        "Missing database connection URL. Set DATABASE_URL (preferred), "
        "SUPABASE_DB_URL, or SUPABASE_DATABASE_URL."
    )


def _ensure_tracking_table(cursor) -> None:
    cursor.execute(
        """
        create table if not exists schema_migrations (
            version text primary key,
            applied_at timestamptz not null default now()
        );
        """
    )


def _is_applied(cursor, version: str) -> bool:
    cursor.execute(
        "select 1 from schema_migrations where version = %s limit 1;",
        (version,),
    )
    return cursor.fetchone() is not None


def _mark_applied(cursor, version: str) -> None:
    cursor.execute(
        "insert into schema_migrations (version) values (%s) on conflict (version) do nothing;",
        (version,),
    )


def main() -> None:
    database_url = _get_database_url()
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print(f"No migration files found in {MIGRATIONS_DIR}")
        return

    with psycopg2.connect(database_url) as conn:
        conn.autocommit = False
        with conn.cursor() as cursor:
            _ensure_tracking_table(cursor)

            for migration_path in migration_files:
                version = migration_path.name
                if _is_applied(cursor, version):
                    print(f"Skipping already-applied migration: {version}")
                    continue

                sql = migration_path.read_text(encoding="utf-8")
                print(f"Applying migration: {version}")
                cursor.execute(sql)
                _mark_applied(cursor, version)

        conn.commit()

    print("Migrations complete")


if __name__ == "__main__":
    main()
