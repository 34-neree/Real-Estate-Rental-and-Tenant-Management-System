from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models.models import Tenant, Payment, PaymentStatus, User, UserRole
from app.schemas.schemas import TenantCreate, TenantUpdate, TenantOut, TenantBalanceOut
from app.utils.auth import get_current_active_user, require_role

router = APIRouter()


@router.post("/", response_model=TenantOut, status_code=201)
def create_tenant(data: TenantCreate, db: Session = Depends(get_db),
                  _: User = Depends(require_role(UserRole.admin, UserRole.manager))):
    if db.query(Tenant).filter(Tenant.email == data.email).first():
        raise HTTPException(status_code=400, detail="Tenant with this email already exists")
    tenant = Tenant(**data.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/", response_model=List[TenantOut])
def list_tenants(
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant)),
):
    q = db.query(Tenant)
    if is_active is not None:
        q = q.filter(Tenant.is_active == is_active)
    if search:
        q = q.filter(
            (Tenant.first_name.ilike(f"%{search}%")) |
            (Tenant.last_name.ilike(f"%{search}%")) |
            (Tenant.email.ilike(f"%{search}%"))
        )
    return q.order_by(Tenant.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.get("/{tenant_id}/balance", response_model=TenantBalanceOut)
def tenant_balance(tenant_id: int, db: Session = Depends(get_db),
                   _: User = Depends(get_current_active_user)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    total_due = db.query(func.sum(Payment.amount_due)).filter(Payment.tenant_id == tenant_id).scalar() or 0.0
    total_paid = db.query(func.sum(Payment.amount)).filter(
        Payment.tenant_id == tenant_id, Payment.status == PaymentStatus.paid).scalar() or 0.0
    overdue_count = db.query(func.count(Payment.id)).filter(
        Payment.tenant_id == tenant_id, Payment.status == PaymentStatus.overdue).scalar() or 0
    return TenantBalanceOut(
        tenant_id=tenant_id, tenant_name=f"{tenant.first_name} {tenant.last_name}",
        total_due=float(total_due), total_paid=float(total_paid),
        outstanding=float(total_due) - float(total_paid), overdue_count=overdue_count)


@router.put("/{tenant_id}", response_model=TenantOut)
def update_tenant(tenant_id: int, data: TenantUpdate, db: Session = Depends(get_db),
                  _: User = Depends(require_role(UserRole.admin, UserRole.manager))):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(tenant_id: int, db: Session = Depends(get_db),
                  _: User = Depends(require_role(UserRole.admin))):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    db.delete(tenant)
    db.commit()
