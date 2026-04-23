from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.models import MaintenanceRequest, MaintenanceStatus, MaintenancePriority, User, UserRole
from app.schemas.schemas import MaintenanceCreate, MaintenanceUpdate, MaintenanceOut
from app.utils.auth import get_current_active_user, require_role

router = APIRouter()


@router.post("/", response_model=MaintenanceOut, status_code=201)
def create_request(data: MaintenanceCreate, db: Session = Depends(get_db),
                   _: User = Depends(get_current_active_user)):
    req = MaintenanceRequest(**data.model_dump())
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/", response_model=List[MaintenanceOut])
def list_requests(
    status: Optional[MaintenanceStatus] = None,
    priority: Optional[MaintenancePriority] = None,
    property_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    q = db.query(MaintenanceRequest)
    if status:
        q = q.filter(MaintenanceRequest.status == status)
    if priority:
        q = q.filter(MaintenanceRequest.priority == priority)
    if property_id:
        q = q.filter(MaintenanceRequest.property_id == property_id)
    if tenant_id:
        q = q.filter(MaintenanceRequest.tenant_id == tenant_id)
    return q.order_by(MaintenanceRequest.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{request_id}", response_model=MaintenanceOut)
def get_request(request_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return req


@router.put("/{request_id}", response_model=MaintenanceOut)
def update_request(request_id: int, data: MaintenanceUpdate, db: Session = Depends(get_db),
                   _: User = Depends(require_role(UserRole.admin, UserRole.manager))):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(req, field, value)
    if data.status == MaintenanceStatus.resolved and not req.resolved_date:
        req.resolved_date = datetime.utcnow()
    db.commit()
    db.refresh(req)
    return req


@router.delete("/{request_id}", status_code=204)
def delete_request(request_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_role(UserRole.admin))):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    db.delete(req)
    db.commit()
