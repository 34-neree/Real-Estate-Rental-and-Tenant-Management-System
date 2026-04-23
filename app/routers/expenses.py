from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Expense, User, UserRole
from app.schemas.schemas import ExpenseCreate, ExpenseUpdate, ExpenseOut
from app.utils.auth import get_current_active_user, require_role

router = APIRouter()


@router.post("/", response_model=ExpenseOut, status_code=201)
def create_expense(data: ExpenseCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant))):
    expense = Expense(**data.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/", response_model=List[ExpenseOut])
def list_expenses(
    property_id: Optional[int] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant)),
):
    q = db.query(Expense)
    if property_id:
        q = q.filter(Expense.property_id == property_id)
    if category:
        q = q.filter(Expense.category.ilike(f"%{category}%"))
    return q.order_by(Expense.date.desc()).offset(skip).limit(limit).all()


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, db: Session = Depends(get_db),
                _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant))):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, data: ExpenseUpdate, db: Session = Depends(get_db),
                   _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant))):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_role(UserRole.admin))):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
