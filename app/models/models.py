from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


# ── Enums ──────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    tenant = "tenant"
    accountant = "accountant"

class PropertyType(str, enum.Enum):
    apartment = "apartment"
    house = "house"
    commercial = "commercial"
    studio = "studio"

class PropertyStatus(str, enum.Enum):
    available = "available"
    occupied = "occupied"
    maintenance = "maintenance"
    inactive = "inactive"

class LeaseStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    terminated = "terminated"
    pending = "pending"

class PaymentStatus(str, enum.Enum):
    paid = "paid"
    pending = "pending"
    overdue = "overdue"
    partial = "partial"

class PaymentMethod(str, enum.Enum):
    cash = "cash"
    bank_transfer = "bank_transfer"
    mobile_money = "mobile_money"
    cheque = "cheque"

class MaintenanceStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    cancelled = "cancelled"

class MaintenancePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    login = "login"
    renew = "renew"
    status_change = "status_change"


# ── Models ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    full_name       = Column(String(100), nullable=False)
    email           = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone           = Column(String(20))
    role            = Column(Enum(UserRole), default=UserRole.tenant)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")


class Property(Base):
    __tablename__ = "properties"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(150), nullable=False)
    address         = Column(String(255), nullable=False)
    city            = Column(String(100))
    state           = Column(String(100))
    zip_code        = Column(String(20))
    property_type   = Column(Enum(PropertyType), default=PropertyType.apartment)
    status          = Column(Enum(PropertyStatus), default=PropertyStatus.available)
    bedrooms        = Column(Integer, default=1)
    bathrooms       = Column(Float, default=1.0)
    size_sqft       = Column(Float)
    rent_amount     = Column(Float, nullable=False)
    deposit_amount  = Column(Float, default=0.0)
    description     = Column(Text)
    amenities       = Column(Text)  # Comma-separated
    manager_id      = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    manager      = relationship("User", foreign_keys=[manager_id])
    leases       = relationship("Lease", back_populates="property")
    maintenance  = relationship("MaintenanceRequest", back_populates="property")


class Tenant(Base):
    __tablename__ = "tenants"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=True)
    first_name       = Column(String(50), nullable=False)
    last_name        = Column(String(50), nullable=False)
    email            = Column(String(100), unique=True, index=True, nullable=False)
    phone            = Column(String(20))
    national_id      = Column(String(50))
    date_of_birth    = Column(DateTime)
    emergency_contact_name  = Column(String(100))
    emergency_contact_phone = Column(String(20))
    occupation       = Column(String(100))
    employer         = Column(String(150))
    monthly_income   = Column(Float)
    credit_score     = Column(Integer)
    references       = Column(Text)
    notes            = Column(Text)
    is_active        = Column(Boolean, default=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    user     = relationship("User", back_populates="tenant")
    leases   = relationship("Lease", back_populates="tenant")
    payments = relationship("Payment", back_populates="tenant")


class Lease(Base):
    __tablename__ = "leases"

    id               = Column(Integer, primary_key=True, index=True)
    property_id      = Column(Integer, ForeignKey("properties.id"), nullable=False)
    tenant_id        = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    start_date       = Column(DateTime, nullable=False)
    end_date         = Column(DateTime, nullable=False)
    rent_amount      = Column(Float, nullable=False)
    deposit_amount   = Column(Float, default=0.0)
    deposit_paid     = Column(Boolean, default=False)
    status           = Column(Enum(LeaseStatus), default=LeaseStatus.pending)
    payment_due_day  = Column(Integer, default=1)  # Day of month
    late_fee         = Column(Float, default=0.0)
    terms            = Column(Text)
    notes            = Column(Text)
    renewed_from_id  = Column(Integer, ForeignKey("leases.id"), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property", back_populates="leases")
    tenant   = relationship("Tenant", back_populates="leases")
    payments = relationship("Payment", back_populates="lease")
    renewed_from = relationship("Lease", remote_side=[id])


class Payment(Base):
    __tablename__ = "payments"

    id              = Column(Integer, primary_key=True, index=True)
    lease_id        = Column(Integer, ForeignKey("leases.id"), nullable=False)
    tenant_id       = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    amount          = Column(Float, nullable=False)
    amount_due      = Column(Float, nullable=False)
    payment_method  = Column(Enum(PaymentMethod), default=PaymentMethod.cash)
    status          = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    payment_date    = Column(DateTime)
    due_date        = Column(DateTime, nullable=False)
    period_month    = Column(Integer)  # 1-12
    period_year     = Column(Integer)
    late_fee        = Column(Float, default=0.0)
    transaction_ref = Column(String(100))
    notes           = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    lease   = relationship("Lease", back_populates="payments")
    tenant  = relationship("Tenant", back_populates="payments")


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id              = Column(Integer, primary_key=True, index=True)
    property_id     = Column(Integer, ForeignKey("properties.id"), nullable=False)
    tenant_id       = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    title           = Column(String(200), nullable=False)
    description     = Column(Text, nullable=False)
    priority        = Column(Enum(MaintenancePriority), default=MaintenancePriority.medium)
    status          = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.open)
    assigned_to     = Column(String(100))
    estimated_cost  = Column(Float)
    actual_cost     = Column(Float)
    scheduled_date  = Column(DateTime)
    resolved_date   = Column(DateTime)
    notes           = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property", back_populates="maintenance")
    tenant   = relationship("Tenant")


class Expense(Base):
    __tablename__ = "expenses"

    id           = Column(Integer, primary_key=True, index=True)
    property_id  = Column(Integer, ForeignKey("properties.id"), nullable=True)
    category     = Column(String(100), nullable=False)  # e.g. repair, tax, insurance
    amount       = Column(Float, nullable=False)
    description  = Column(Text)
    date         = Column(DateTime, nullable=False)
    vendor       = Column(String(150))
    receipt_ref  = Column(String(100))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    property = relationship("Property")


class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    title      = Column(String(200), nullable=False)
    message    = Column(Text, nullable=False)
    category   = Column(String(50), default="info")  # info, warning, success, error
    is_read    = Column(Boolean, default=False)
    link       = Column(String(255), nullable=True)  # optional deep-link
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    action      = Column(Enum(AuditAction), nullable=False)
    entity_type = Column(String(50), nullable=False)  # e.g. "lease", "payment"
    entity_id   = Column(Integer, nullable=True)
    details     = Column(Text)
    ip_address  = Column(String(45))
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
