from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import (
    Property, Tenant, Lease, Payment, MaintenanceRequest, Expense,
    PropertyStatus, LeaseStatus, PaymentStatus, User, UserRole
)
from app.utils.auth import require_role

router = APIRouter()


@router.get("/dashboard")
def dashboard_summary(db: Session = Depends(get_db),
                      _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant))):
    total_properties = db.query(Property).count()
    available = db.query(Property).filter(Property.status == PropertyStatus.available).count()
    occupied = db.query(Property).filter(Property.status == PropertyStatus.occupied).count()
    total_tenants = db.query(Tenant).filter(Tenant.is_active == True).count()
    active_leases = db.query(Lease).filter(Lease.status == LeaseStatus.active).count()
    overdue_payments = db.query(Payment).filter(
        Payment.status.in_([PaymentStatus.pending, PaymentStatus.partial]),
        Payment.due_date < datetime.utcnow()
    ).count()
    open_maintenance = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.status.in_(["open", "in_progress"])
    ).count()
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    monthly_income = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.paid,
        Payment.period_month == current_month,
        Payment.period_year == current_year,
    ).scalar() or 0.0
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        extract("month", Expense.date) == current_month,
        extract("year", Expense.date) == current_year,
    ).scalar() or 0.0

    return {
        "total_properties": total_properties,
        "available": available,
        "occupied": occupied,
        "occupancy_rate": round((occupied / total_properties * 100) if total_properties else 0, 2),
        "total_active_tenants": total_tenants,
        "active_leases": active_leases,
        "overdue_payments": overdue_payments,
        "open_maintenance": open_maintenance,
        "monthly_income": float(monthly_income),
        "monthly_expenses": float(total_expenses),
        "net_income": float(monthly_income) - float(total_expenses),
    }


@router.get("/income")
def income_report(
    year: int = Query(default=datetime.utcnow().year),
    property_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant)),
):
    q = db.query(
        Payment.period_month,
        func.sum(Payment.amount).label("total_income"),
        func.count(Payment.id).label("payment_count"),
    ).filter(Payment.status == PaymentStatus.paid, Payment.period_year == year)
    if property_id:
        q = q.join(Lease).filter(Lease.property_id == property_id)
    rows = q.group_by(Payment.period_month).order_by(Payment.period_month).all()
    return {
        "year": year, "property_id": property_id,
        "monthly_breakdown": [
            {"month": r.period_month, "total_income": float(r.total_income or 0), "payments": r.payment_count}
            for r in rows
        ],
        "annual_total": sum(float(r.total_income or 0) for r in rows),
    }


@router.get("/expenses")
def expense_report(
    year: int = Query(default=datetime.utcnow().year),
    property_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant)),
):
    q = db.query(Expense.category, func.sum(Expense.amount).label("total")).filter(
        extract("year", Expense.date) == year)
    if property_id:
        q = q.filter(Expense.property_id == property_id)
    rows = q.group_by(Expense.category).all()
    return {
        "year": year,
        "by_category": [{"category": r.category, "total": float(r.total or 0)} for r in rows],
        "total_expenses": sum(float(r.total or 0) for r in rows),
    }


@router.get("/profit-loss")
def profit_loss_report(
    year: int = Query(default=datetime.utcnow().year),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant)),
):
    """Monthly profit/loss: income minus expenses."""
    monthly = []
    for m in range(1, 13):
        income = db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.paid, Payment.period_month == m, Payment.period_year == year
        ).scalar() or 0.0
        expenses = db.query(func.sum(Expense.amount)).filter(
            extract("month", Expense.date) == m, extract("year", Expense.date) == year
        ).scalar() or 0.0
        monthly.append({"month": m, "income": float(income), "expenses": float(expenses),
                        "profit": float(income) - float(expenses)})
    return {"year": year, "monthly": monthly,
            "annual_income": sum(m["income"] for m in monthly),
            "annual_expenses": sum(m["expenses"] for m in monthly),
            "annual_profit": sum(m["profit"] for m in monthly)}


@router.get("/arrears")
def arrears_report(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant)),
):
    """List tenants with overdue balances."""
    tenants = db.query(Tenant).filter(Tenant.is_active == True).all()
    result = []
    for t in tenants:
        overdue_amount = db.query(func.sum(Payment.amount_due - Payment.amount)).filter(
            Payment.tenant_id == t.id,
            Payment.status.in_([PaymentStatus.overdue, PaymentStatus.pending]),
            Payment.due_date < datetime.utcnow()
        ).scalar() or 0.0
        if overdue_amount > 0:
            result.append({
                "tenant_id": t.id, "tenant_name": f"{t.first_name} {t.last_name}",
                "email": t.email, "overdue_amount": float(overdue_amount)
            })
    return sorted(result, key=lambda x: x["overdue_amount"], reverse=True)


@router.get("/occupancy")
def occupancy_report(db: Session = Depends(get_db),
                     _: User = Depends(require_role(UserRole.admin, UserRole.manager))):
    props = db.query(Property).all()
    result = []
    for p in props:
        active_lease = db.query(Lease).filter(
            Lease.property_id == p.id, Lease.status == LeaseStatus.active).first()
        result.append({
            "property_id": p.id, "property_name": p.name, "status": p.status,
            "rent_amount": p.rent_amount,
            "tenant": f"{active_lease.tenant.first_name} {active_lease.tenant.last_name}" if active_lease and active_lease.tenant else None,
            "lease_end": active_lease.end_date.isoformat() if active_lease else None,
        })
    return result


@router.get("/leases/expiring")
def expiring_leases(
    days: int = Query(default=30),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager)),
):
    threshold = datetime.utcnow() + timedelta(days=days)
    leases = db.query(Lease).filter(
        Lease.status == LeaseStatus.active, Lease.end_date <= threshold, Lease.end_date >= datetime.utcnow()
    ).all()
    return [
        {"lease_id": l.id, "property_id": l.property_id, "tenant_id": l.tenant_id,
         "end_date": l.end_date.isoformat(), "days_left": (l.end_date - datetime.utcnow()).days}
        for l in leases
    ]


@router.get("/payments/summary")
def payment_summary(
    month: int = Query(default=datetime.utcnow().month),
    year: int = Query(default=datetime.utcnow().year),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.accountant)),
):
    paid = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.paid, Payment.period_month == month, Payment.period_year == year).scalar() or 0
    pending = db.query(func.sum(Payment.amount_due)).filter(
        Payment.status == PaymentStatus.pending, Payment.period_month == month, Payment.period_year == year).scalar() or 0
    overdue = db.query(func.count(Payment.id)).filter(
        Payment.status.in_([PaymentStatus.pending, PaymentStatus.partial]),
        Payment.due_date < datetime.utcnow(), Payment.period_month == month, Payment.period_year == year).scalar() or 0
    return {"month": month, "year": year, "collected": float(paid), "outstanding": float(pending), "overdue_count": overdue}
