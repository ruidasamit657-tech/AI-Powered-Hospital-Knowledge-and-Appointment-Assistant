#!/usr/bin/env python3
"""
Create an admin user.
Run: python scripts/create_admin.py
"""

# pylint: disable=wrong-import-position,import-error,no-name-in-module

import sys
from pathlib import Path
from getpass import getpass

# Ensure project root is on sys.path so `app` can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # type: ignore[import-not-found]
from app.crud.user import (  # type: ignore[import-not-found]
    get_user_by_username,
    get_user_by_email,
    create_user,
)
from app.schemas.user import UserCreate  # type: ignore[import-not-found]
from app.db.models.user import UserRole  # type: ignore[import-not-found]


def main() -> None:
    """Create an admin user interactively."""
    db = SessionLocal()
    try:
        print("=== Create Admin User ===")
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        full_name = input("Full name: ").strip()
        password = getpass("Password: ")
        confirm = getpass("Confirm password: ")

        if password != confirm:
            print("Passwords do not match.")
            return

        if get_user_by_username(db, username):
            print("Username already exists.")
            return
        if get_user_by_email(db, email):
            print("Email already registered.")
            return

        user_in = UserCreate(
            username=username,
            email=email,
            full_name=full_name,
            password=password,
            role=UserRole.ADMIN,
        )
        user = create_user(db, user_in)
        print(f"Admin user '{user.username}' created successfully with id {user.id}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()