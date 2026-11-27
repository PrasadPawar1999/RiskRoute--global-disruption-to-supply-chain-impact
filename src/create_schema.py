"""
Phase 2, step 1: create all ChainSight tables in MySQL.

Run from the project root:
    python src/create_schema.py

Reads sql/01_schema.sql and runs it. Safe to run again: it drops and
recreates the tables (any data in them is deleted).
"""
import re
from pathlib import Path

from sqlalchemy import text

from db import DB_NAME, get_engine

SCHEMA_FILE = Path(__file__).resolve().parent.parent / "sql" / "01_schema.sql"


def split_statements(sql: str) -> list[str]:
    """Remove -- comments and split the file into individual statements."""
    sql = re.sub(r"--[^\n]*", "", sql)
    return [s.strip() for s in sql.split(";") if s.strip()]


def main():
    # Make sure the database exists first
    with get_engine(with_database=False).begin() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))

    statements = split_statements(SCHEMA_FILE.read_text(encoding="utf-8"))
    engine = get_engine()

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))

        tables = conn.execute(text("SHOW TABLES")).fetchall()

    print(f"✅ Schema created: {len(tables)} tables")
    for (name,) in tables:
        print(f"   - {name}")


if __name__ == "__main__":
    main()
