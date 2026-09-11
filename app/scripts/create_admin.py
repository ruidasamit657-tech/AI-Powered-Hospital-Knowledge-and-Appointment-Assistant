#!/usr/bin/env python
"""
Script to create an admin user.
Run: python -m app.scripts.create_admin
"""

import logging
from pathlib import Path
import sys

# Add project root to path before loading app modules
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position, import-error, no-name-in-module
from sqlalchemy.exc import SQLAlchemyError
from app.crud.user import create_user, get_user_by_username  # type: ignore # noqa: F401
from app.db.session import SessionLocal                      # type: ignore # noqa: F401
from app.schemas.user import UserCreate                      # type: ignore # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user():
    """Create an admin user if it doesn't exist"""
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        admin = get_user_by_username(db, "admin")
        
        if admin:
            logger.info("Admin user already exists")
            print("\nAdmin user already exists!")
            print("Username: admin")
            print("To reset password, delete the user and run this script again.")
            return
        
        # Create admin user
        admin_data = UserCreate(
            email="admin@hospital.com",
            username="admin",
            full_name="System Administrator",
            password="Admin123!",
            role="admin"
        )
        
        create_user(db, admin_data)
        
        logger.info("Admin user created successfully!")
        print("\n" + "="*50)
        print("ADMIN USER CREATED")
        print("="*50)
        print("Username: admin")
        print("Email: admin@hospital.com")
        print("Password: Admin123!")
        print("Role: admin")
        print("="*50)
        print("\nIMPORTANT: Please change the password after first login!\n\n")
        
    except SQLAlchemyError as e:
        logger.error("Database error creating admin user: %s", e)
        print(f"Database Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
