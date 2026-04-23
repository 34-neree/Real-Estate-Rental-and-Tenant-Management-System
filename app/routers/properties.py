from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Property, PropertyStatus, PropertyType, User, UserRole
from app.schemas.schemas import PropertyCreate, PropertyUpdate, PropertyOut
from app.utils.auth import get_current_active_user, require_role

router = APIRouter()


@router.post("/", response_model=PropertyOut, status_code=201)
def create_property(data: PropertyCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_role(UserRole.admin, UserRole.manager))):
    prop = Property(**data.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@router.get("/", response_model=List[PropertyOut])
def list_properties(
    status: Optional[PropertyStatus] = None,
    property_type: Optional[PropertyType] = None,
    min_rent: Optional[float] = None,
    max_rent: Optional[float] = None,
    city: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    q = db.query(Property)
    if status:
        q = q.filter(Property.status == status)
    if property_type:
        q = q.filter(Property.property_type == property_type)
    if min_rent:
        q = q.filter(Property.rent_amount >= min_rent)
    if max_rent:
        q = q.filter(Property.rent_amount <= max_rent)
    if city:
        q = q.filter(Property.city.ilike(f"%{city}%"))
    return q.offset(skip).limit(limit).all()


@router.get("/available", response_model=List[PropertyOut])
def list_available(db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    return db.query(Property).filter(Property.status == PropertyStatus.available).all()


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(property_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.put("/{property_id}", response_model=PropertyOut)
def update_property(property_id: int, data: PropertyUpdate, db: Session = Depends(get_db),
                    _: User = Depends(require_role(UserRole.admin, UserRole.manager))):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prop, field, value)
    db.commit()
    db.refresh(prop)
    return prop


@router.delete("/{property_id}", status_code=204)
def delete_property(property_id: int, db: Session = Depends(get_db),
                    _: User = Depends(require_role(UserRole.admin))):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(prop)
    db.commit()
