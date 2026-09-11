from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.sql.functions import count
from app.crud.crud.base import CRUDBase
from app.db.models.department import Department
from app.db.schemas.department import DepartmentCreate, DepartmentUpdate

class CRUDDepartment(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Department]:
        return db.query(Department).filter(Department.name == name).first()

    def search_departments(self, db: Session, *, search_term: str) -> List[Department]:
        return db.query(Department).filter(
            or_(
                Department.name.ilike(f"%{search_term}%"),
                Department.description.ilike(f"%{search_term}%")
            )
        ).all()

    def get_with_doctors(self, db: Session, *, department_id: str) -> Optional[Department]:
        return db.query(Department).filter(Department.id == department_id).first()

    def get_all_with_counts(self, db: Session) -> List[dict]:
        from app.db.models.doctor import Doctor
        results = db.query(
            Department,
            count(Doctor.id).label('doctor_count')
        ).outerjoin(Doctor, Doctor.department_id == Department.id).group_by(Department.id).all()
        
        return [
            {
                "department": dept,
                "doctor_count": count
            }
            for dept, count in results
        ]

department_crud = CRUDDepartment(Department)