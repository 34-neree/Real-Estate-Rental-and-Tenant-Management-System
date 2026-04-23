from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from app.models.models import (
    UserRole, PropertyType, PropertyStatus,
    LeaseStatus, PaymentStatus, PaymentMethod,
    MaintenanceStatus, MaintenancePriority, AuditAction
)


# ── Token ──────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── User ───────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole = UserRole.tenant

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ── Property ───────────────────────────────────────────────────────────────────

class PropertyBase(BaseModel):
    name: str
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    property_type: PropertyType = PropertyType.apartment
    bedrooms: int = 1
    bathrooms: float = 1.0
    size_sqft: Optional[float] = None
    rent_amount: float
    deposit_amount: float = 0.0
    description: Optional[str] = None
    amenities: Optional[str] = None
    manager_id: Optional[int] = None

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    property_type: Optional[PropertyType] = None
    status: Optional[PropertyStatus] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    size_sqft: Optional[float] = None
    rent_amount: Optional[float] = None
    deposit_amount: Optional[float] = None
    description: Optional[str] = None
    amenities: Optional[str] = None
    manager_id: Optional[int] = None

class PropertyOut(PropertyBase):
    id: int
    status: PropertyStatus
    created_at: datetime
    class Config:
        from_attributes = True


# ── Tenant ─────────────────────────────────────────────────────────────────────

class TenantBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    national_id: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    monthly_income: Optional[float] = None
    credit_score: Optional[int] = None
    references: Optional[str] = None
    notes: Optional[str] = None

class TenantCreate(TenantBase):
    pass

class TenantUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    monthly_income: Optional[float] = None
    credit_score: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class TenantOut(TenantBase):
    id: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class TenantBalanceOut(BaseModel):
    tenant_id: int
    tenant_name: str
    total_due: float
    total_paid: float
    outstanding: float
    overdue_count: int


# ── Lease ──────────────────────────────────────────────────────────────────────

class LeaseBase(BaseModel):
    property_id: int
    tenant_id: int
    start_date: datetime
    end_date: datetime
    rent_amount: float
    deposit_amount: float = 0.0
    deposit_paid: bool = False
    payment_due_day: int = 1
    late_fee: float = 0.0
    terms: Optional[str] = None
    notes: Optional[str] = None

class LeaseCreate(LeaseBase):
    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("start_date")
        if start and v <= start:
            raise ValueError("end_date must be after start_date")
        return v

class LeaseUpdate(BaseModel):
    end_date: Optional[datetime] = None
    rent_amount: Optional[float] = None
    deposit_paid: Optional[bool] = None
    status: Optional[LeaseStatus] = None
    payment_due_day: Optional[int] = None
    late_fee: Optional[float] = None
    terms: Optional[str] = None
    notes: Optional[str] = None

class LeaseRenew(BaseModel):
    new_start_date: datetime
    new_end_date: datetime
    new_rent_amount: Optional[float] = None
    notes: Optional[str] = None

    @field_validator("new_end_date")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("new_start_date")
        if start and v <= start:
            raise ValueError("new_end_date must be after new_start_date")
        return v

class LeaseOut(LeaseBase):
    id: int
    status: LeaseStatus
    renewed_from_id: Optional[int] = None
    created_at: datetime
    property: Optional[PropertyOut] = None
    tenant: Optional[TenantOut] = None
    class Config:
        from_attributes = True


# ── Payment ────────────────────────────────────────────────────────────────────

class PaymentBase(BaseModel):
    lease_id: int
    tenant_id: int
    amount: float
    amount_due: float
    payment_method: PaymentMethod = PaymentMethod.cash
    due_date: datetime
    period_month: Optional[int] = None
    period_year: Optional[int] = None
    late_fee: float = 0.0
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    payment_method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None
    payment_date: Optional[datetime] = None
    late_fee: Optional[float] = None
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None

class PaymentOut(PaymentBase):
    id: int
    status: PaymentStatus
    payment_date: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True

class TenantPaymentSummary(BaseModel):
    tenant_id: int
    tenant_name: str
    total_paid: float
    total_outstanding: float
    overdue_count: int
    last_payment_date: Optional[datetime] = None


# ── Maintenance ────────────────────────────────────────────────────────────────

class MaintenanceBase(BaseModel):
    property_id: int
    tenant_id: Optional[int] = None
    title: str
    description: str
    priority: MaintenancePriority = MaintenancePriority.medium
    assigned_to: Optional[str] = None
    estimated_cost: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    notes: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[MaintenancePriority] = None
    status: Optional[MaintenanceStatus] = None
    assigned_to: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    notes: Optional[str] = None

class MaintenanceOut(MaintenanceBase):
    id: int
    status: MaintenanceStatus
    actual_cost: Optional[float]
    resolved_date: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True


# ── Expense ────────────────────────────────────────────────────────────────────

class ExpenseBase(BaseModel):
    property_id: Optional[int] = None
    category: str
    amount: float
    description: Optional[str] = None
    date: datetime
    vendor: Optional[str] = None
    receipt_ref: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    property_id: Optional[int] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    vendor: Optional[str] = None
    receipt_ref: Optional[str] = None

class ExpenseOut(ExpenseBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Notification ───────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    category: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ── Audit Log ──────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: AuditAction
    entity_type: str
    entity_id: Optional[int]
    details: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# Resolve forward reference
LoginResponse.model_rebuild()
