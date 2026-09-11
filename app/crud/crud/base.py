from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

TModel = TypeVar("TModel")
TCreateSchema = TypeVar("TCreateSchema", bound=BaseModel)
TUpdateSchema = TypeVar("TUpdateSchema", bound=BaseModel)

class CRUDBase(Generic[TModel, TCreateSchema, TUpdateSchema]):
    def __init__(self, model: Type[TModel]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        """
        self.model = model

    def get(self, db: Session, object_id: str) -> Optional[TModel]:
        return db.query(self.model).filter(self.model.id == object_id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[TModel]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: TCreateSchema) -> TModel:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: TModel,
        obj_in: Union[TUpdateSchema, Dict[str, Any]]
    ) -> TModel:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, object_id: str) -> Optional[TModel]:
        obj = db.query(self.model).get(object_id)
        db.delete(obj)
        db.commit()
        return obj

    def exists(self, db: Session, **kwargs) -> bool:
        query = db.query(self.model)
        for key, value in kwargs.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.first() is not None