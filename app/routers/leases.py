from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import Lease, Property, Tenant, PropertyStatus, LeaseStatus, User, UserRole, AuditLog, AuditAction
from app.schemas.schemas import LeaseCreate, LeaseUpdate, LeaseOut, LeaseRenew
from app.utils.auth import get_current_active_user, require_role

router = APIRouter()


@router.post("/", response_model=LeaseOut, status_code=201)
def create_lease(data: LeaseCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role(UserRole.admin, UserRole.manager))):
    # Validate property exists
    prop = db.query(Property).filter(Property.id == data.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.status == PropertyStatus.occupied:
        raise HTTPException(status_code=400, detail="Property is already occupied")

    # Validate tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == data.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Prevent double-booking: check if tenant already has active lease on this property
    existing = db.query(Lease).filter(
        Lease.property_id == data.property_id,
        Lease.tenant_id == data.tenant_id,
        Lease.status == LeaseStatus.active,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant already has an active lease on this property")

    lease = Lease(**data.model_dump(), status=LeaseStatus.active)
    db.add(lease)

    prop.status = PropertyStatus.occupied

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id, action=AuditAction.create,
        entity_type="lease", entity_id=None,
        details=f"Lease created for tenant {data.tenant_id} on property {data.property_id}"
    ))

    db.commit()
    db.refresh(lease)

    # Update audit log with the lease id
    log = db.query(AuditLog).filter(
        AuditLog.entity_type == "lease", AuditLog.entity_id == None
    ).order_by(AuditLog.id.desc()).first()
    if log:
        log.entity_id = lease.id
        db.commit()

    return lease


@router.get("/", response_model=List[LeaseOut])
def list_leases(
    status: Optional[LeaseStatus] = None,
    tenant_id: Optional[int] = None,
    property_id: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    q = db.query(Lease)
    if status:
        q = q.filter(Lease.status == status)
    if tenant_id:
        q = q.filter(Lease.tenant_id == tenant_id)
    if property_id:
        q = q.filter(Lease.property_id == property_id)
    return q.order_by(Lease.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/expiring-soon", response_model=List[LeaseOut])
def expiring_soon(
    days: int = Query(default=30, description="Alert threshold in days"),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager)),
):
    threshold = datetime.utcnow() + timedelta(days=days)
    return (
        db.query(Lease)
        .filter(Lease.status == LeaseStatus.active)
        .filter(Lease.end_date <= threshold)
        .filter(Lease.end_date >= datetime.utcnow())
        .order_by(Lease.end_date.asc())
        .all()
    )


@router.get("/{lease_id}", response_model=LeaseOut)
def get_lease(lease_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    return lease


@router.put("/{lease_id}", response_model=LeaseOut)
def update_lease(lease_id: int, data: LeaseUpdate, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role(UserRole.admin, UserRole.manager))):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lease, field, value)

    # If lease is terminated or expired, free the property
    if data.status in (LeaseStatus.terminated, LeaseStatus.expired):
        prop = db.query(Property).filter(Property.id == lease.property_id).first()
        if prop:
            prop.status = PropertyStatus.available

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id, action=AuditAction.update,
        entity_type="lease", entity_id=lease_id,
        details=f"Lease updated: {data.model_dump(exclude_unset=True)}"
    ))

    db.commit()
    db.refresh(lease)
    return lease


@router.post("/{lease_id}/renew", response_model=LeaseOut, status_code=201)
def renew_lease(lease_id: int, data: LeaseRenew, db: Session = Depends(get_db),
                current_user: User = Depends(require_role(UserRole.admin, UserRole.manager))):
    """Renew an existing lease by creating a new one linked to the old."""
    old_lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not old_lease:
        raise HTTPException(status_code=404, detail="Original lease not found")
    if old_lease.status not in (LeaseStatus.active, LeaseStatus.expired):
        raise HTTPException(status_code=400, detail="Only active or expired leases can be renewed")

    # Expire the old lease
    old_lease.status = LeaseStatus.expired

    new_lease = Lease(
        property_id=old_lease.property_id,
        tenant_id=old_lease.tenant_id,
        start_date=data.new_start_date,
        end_date=data.new_end_date,
        rent_amount=data.new_rent_amount or old_lease.rent_amount,
        deposit_amount=old_lease.deposit_amount,
        deposit_paid=old_lease.deposit_paid,
        payment_due_day=old_lease.payment_due_day,
        late_fee=old_lease.late_fee,
        terms=old_lease.terms,
        notes=data.notes or old_lease.notes,
        status=LeaseStatus.active,
        renewed_from_id=old_lease.id,
    )
    db.add(new_lease)

    # Keep property occupied
    prop = db.query(Property).filter(Property.id == old_lease.property_id).first()
    if prop:
        prop.status = PropertyStatus.occupied

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id, action=AuditAction.renew,
        entity_type="lease", entity_id=lease_id,
        details=f"Lease renewed from #{lease_id}"
    ))

    db.commit()
    db.refresh(new_lease)
    return new_lease


@router.delete("/{lease_id}", status_code=204)
def delete_lease(lease_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role(UserRole.admin))):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    # Free the property if the lease was active
    if lease.status == LeaseStatus.active:
        prop = db.query(Property).filter(Property.id == lease.property_id).first()
        if prop:
            prop.status = PropertyStatus.available

    db.delete(lease)
    db.commit()
