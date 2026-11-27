"""
Phase 1 check: can Python talk to MySQL?

Run from the project root:
    python src/test_connection.py

It reads your settings from .env, creates the 'chainsight' database
if it doesn't exist yet, and prints the MySQL version.
"""
from sqlalchemy import text

from db import DB_NAME, get_engine


def main():
    # 1. Connect to the MySQL server (no database selected yet)
    engine = get_engine(with_database=False)

    with engine.connect() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
        print(f"✅ Connected to MySQL server, version {version}")

        # 2. Create the project database if it isn't there yet
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
        print(f"✅ Database '{DB_NAME}' is ready")

    # 3. Connect to the project database itself and run a test query
    db_engine = get_engine()
    with db_engine.connect() as conn:
        current = conn.execute(text("SELECT DATABASE()")).scalar()
        print(f"✅ Now using database: {current}")

    print("\n🎉 Setup works. You're ready for Phase 2.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ Connection failed:")
        print(f"   {e}")
        print("\nCheck that:")
        print("  - MySQL is running")
        print("  - your password in .env is correct")
        print("  - you ran: pip install -r requirements.txt")
