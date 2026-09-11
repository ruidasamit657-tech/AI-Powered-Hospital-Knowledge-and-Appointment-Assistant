#!/usr/bin/env python3
"""
Check local setup: .env, database, folders.
Run: python scripts/check_local_setup.py
"""

import sys
from pathlib import Path

# Allow running this script directly from the project root
sys.path.append(str(Path(__file__).resolve().parent.parent))

# pylint: disable=wrong-import-position
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import engine


def check_env() -> bool:
    """Check that a .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found. Copy .env.example to .env and fill values.")
        return False
    print("✅ .env file found.")
    return True


def check_settings() -> bool:
    """Check that required settings are loaded."""
    missing = []
    if not settings.DATABASE_URL:
        missing.append("DATABASE_URL")
    if not settings.SECRET_KEY:
        missing.append("SECRET_KEY")

    if missing:
        print(f"❌ Missing required settings: {', '.join(missing)}")
        return False

    print(f"✅ Settings loaded (app name: {settings.APP_NAME}).")
    return True


def check_database() -> bool:
    """Check that the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful.")
        return True
    except SQLAlchemyError as exc:
        print(f"❌ Database connection failed: {exc}")
        return False


def check_folders() -> bool:
    """Check that required data folders exist."""
    folders = [
        "data/knowledge_base",
        "data/storage",
        "data/vector_index",
    ]
    all_ok = True
    for folder in folders:
        path = Path(folder)
        try:
            exists = path.exists() and path.is_dir()
        except OSError as exc:
            print(f"❌ Error checking folder {folder}: {exc}")
            all_ok = False
            continue

        if exists:
            print(f"✅ Folder exists: {folder}")
        else:
            print(f"❌ Missing folder: {folder}")
            all_ok = False
    return all_ok


def main() -> None:
    """Run all setup checks."""
    print("=== Local Setup Check ===\n")
    ok = True
    ok &= check_env()
    ok &= check_settings()
    ok &= check_database()
    ok &= check_folders()

    if ok:
        print("\n🎉 All checks passed. You are ready to run the app.")
    else:
        print("\n⚠️  Some checks failed. Fix the issues above and re-run.")


if __name__ == "__main__":
    main()