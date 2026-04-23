from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.models import Payment, Lease, Tenant, PaymentStatus, User, UserRole
from app.schemas.schemas import PaymentCreate, PaymentUpdate, PaymentOut, TenantPaymentSummary
from app.utils.auth import get_current_active_user, require_role

router = APIRouter()


@router.post("/", response_model=PaymentOut, status_code=201)
def create_payment(data: PaymentCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant))):
    # Validate lease exists
    lease = db.query(Lease).filter(Lease.id == data.lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    # Validate tenant exists and matches lease
    tenant = db.query(Tenant).filter(Tenant.id == data.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if lease.tenant_id != data.tenant_id:
        raise HTTPException(status_code=400, detail="Tenant does not match the lease")

    payment = Payment(**data.model_dump())
    # Determine initial status
    if data.amount >= data.amount_due:
        payment.status = PaymentStatus.pending  # Will be marked paid when payment_date is set
    else:
        payment.status = PaymentStatus.partial
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/", response_model=List[PaymentOut])
def list_payments(
    status: Optional[PaymentStatus] = None,
    tenant_id: Optional[int] = None,
    lease_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    q = db.query(Payment)
    if status:
        q = q.filter(Payment.status == status)
    if tenant_id:
        q = q.filter(Payment.tenant_id == tenant_id)
    if lease_id:
        q = q.filter(Payment.lease_id == lease_id)
    if year:
        q = q.filter(Payment.period_year == year)
    if month:
        q = q.filter(Payment.period_month == month)
    return q.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/overdue", response_model=List[PaymentOut])
def list_overdue(db: Session = Depends(get_db),
                 _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant))):
    now = datetime.utcnow()
    return (
        db.query(Payment)
        .filter(Payment.due_date < now)
        .filter(Payment.status.in_([PaymentStatus.pending, PaymentStatus.partial]))
        .order_by(Payment.due_date.asc())
        .all()
    )


@router.put("/mark-overdue")
def mark_overdue_payments(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager)),
):
    """Batch-mark all pending payments past their due_date as overdue."""
    now = datetime.utcnow()
    count = (
        db.query(Payment)
        .filter(Payment.due_date < now)
        .filter(Payment.status.in_([PaymentStatus.pending, PaymentStatus.partial]))
        .update({Payment.status: PaymentStatus.overdue}, synchronize_session="fetch")
    )
    db.commit()
    return {"message": f"{count} payment(s) marked as overdue"}


@router.get("/tenant/{tenant_id}/summary", response_model=TenantPaymentSummary)
def tenant_payment_summary(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Get payment summary for a specific tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    total_paid = db.query(func.sum(Payment.amount)).filter(
        Payment.tenant_id == tenant_id,
        Payment.status == PaymentStatus.paid,
    ).scalar() or 0.0

    total_outstanding = db.query(func.sum(Payment.amount_due - Payment.amount)).filter(
        Payment.tenant_id == tenant_id,
        Payment.status.in_([PaymentStatus.pending, PaymentStatus.partial, PaymentStatus.overdue]),
    ).scalar() or 0.0

    overdue_count = db.query(func.count(Payment.id)).filter(
        Payment.tenant_id == tenant_id,
        Payment.status == PaymentStatus.overdue,
    ).scalar() or 0

    last_payment = db.query(func.max(Payment.payment_date)).filter(
        Payment.tenant_id == tenant_id,
        Payment.status == PaymentStatus.paid,
    ).scalar()

    return TenantPaymentSummary(
        tenant_id=tenant_id,
        tenant_name=f"{tenant.first_name} {tenant.last_name}",
        total_paid=float(total_paid),
        total_outstanding=float(total_outstanding),
        overdue_count=overdue_count,
        last_payment_date=last_payment,
    )


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.put("/{payment_id}", response_model=PaymentOut)
def update_payment(payment_id: int, data: PaymentUpdate, db: Session = Depends(get_db),
                   _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant))):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)
    # Auto-mark as paid if payment date provided and amount is enough
    if data.payment_date and payment.amount >= payment.amount_due:
        payment.status = PaymentStatus.paid
    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{payment_id}", status_code=204)
def delete_payment(payment_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_role(UserRole.admin))):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    db.delete(payment)
    db.commit()
