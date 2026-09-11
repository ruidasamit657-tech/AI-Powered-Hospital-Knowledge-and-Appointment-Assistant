"""
User CRUD operations
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.crud.crud.base import CRUDBase
from app.db.models.user import User, UserRole
from app.db.schemas.user import UserCreate, UserUpdate
from app.core.security import security


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            id=obj_in.id if hasattr(obj_in, 'id') else None,
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=security.get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            role=UserRole(obj_in.role) if obj_in.role else UserRole.PATIENT,
            is_active=True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not security.verify_password(password, user.hashed_password):
            return None
        return user

    def change_password(self, db: Session, *, user_id: str, new_password: str) -> User:
        user = self.get(db, object_id=user_id)
        if not user:
            return None
        user.hashed_password = security.get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_users_by_role(self, db: Session, *, role: UserRole) -> List[User]:
        return db.query(User).filter(User.role == role).all()

    def get_active_users(self, db: Session) -> List[User]:
        return db.query(User).filter(User.is_active == True).all()

    def toggle_active(self, db: Session, *, user_id: str) -> User:
        user = self.get(db, object_id=user_id)
        if user:
            user.is_active = not user.is_active
            db.add(user)
            db.commit()
            db.refresh(user)
        return user


user_crud = CRUDUser(User)


def create_user(db: Session, user_in: UserCreate) -> User:
    """Helper function to map old test fixture calls to the new CRUD pattern"""
    return user_crud.create(db, obj_in=user_in)