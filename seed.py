"""
Seed script – populates the database with demo data.
Run:  python seed.py
"""
from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models.models import (
    User, Property, Tenant, Lease, Payment, MaintenanceRequest, Expense,
    UserRole, PropertyType, PropertyStatus, LeaseStatus,
    PaymentStatus, PaymentMethod, MaintenancePriority, MaintenanceStatus,
)
from app.utils.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def seed():
    # ── Users ──────────────────────────────────────────────────────────────────
    admin = User(full_name="Admin User", email="admin@rental.com",
                 hashed_password=hash_password("admin123"), role=UserRole.admin, phone="0780000001")
    manager = User(full_name="Jane Manager", email="manager@rental.com",
                   hashed_password=hash_password("manager123"), role=UserRole.manager, phone="0780000002")
    accountant = User(full_name="Bob Accountant", email="accountant@rental.com",
                      hashed_password=hash_password("accountant123"), role=UserRole.accountant, phone="0780000003")
    db.add_all([admin, manager, accountant])
    db.commit()

    # ── Properties ─────────────────────────────────────────────────────────────
    props = [
        Property(name="Sunset Apartment 1A", address="12 Kigali Heights", city="Kigali", state="Kigali",
                 property_type=PropertyType.apartment, bedrooms=2, bathrooms=1.0, size_sqft=850,
                 rent_amount=500, deposit_amount=1000, status=PropertyStatus.occupied,
                 amenities="WiFi, Parking, Security", manager_id=manager.id),
        Property(name="Green Villa 3B", address="45 Remera Road", city="Kigali", state="Kigali",
                 property_type=PropertyType.house, bedrooms=3, bathrooms=2.0, size_sqft=1400,
                 rent_amount=900, deposit_amount=1800, status=PropertyStatus.occupied,
                 amenities="Garden, Garage, Security", manager_id=manager.id),
        Property(name="City Studio 7", address="78 Nyarutarama Ave", city="Kigali", state="Kigali",
                 property_type=PropertyType.studio, bedrooms=1, bathrooms=1.0, size_sqft=400,
                 rent_amount=300, deposit_amount=600, status=PropertyStatus.available,
                 amenities="WiFi, Laundry", manager_id=manager.id),
        Property(name="Business Suite 2F", address="5 CBD Tower, KN 4 Ave", city="Kigali", state="Kigali",
                 property_type=PropertyType.commercial, bedrooms=0, bathrooms=1.0, size_sqft=600,
                 rent_amount=1200, deposit_amount=2400, status=PropertyStatus.available,
                 amenities="Reception, Parking, CCTV", manager_id=manager.id),
    ]
    db.add_all(props)
    db.commit()

    # ── Tenants ────────────────────────────────────────────────────────────────
    tenants = [
        Tenant(first_name="Alice", last_name="Mukamana", email="alice@email.com", phone="0781111111",
               national_id="1199780012345678", occupation="Engineer", employer="TechCorp",
               monthly_income=2000, emergency_contact_name="John Mukamana", emergency_contact_phone="0782222222"),
        Tenant(first_name="Eric", last_name="Nshimiyimana", email="eric@email.com", phone="0783333333",
               national_id="1199880087654321", occupation="Teacher", employer="FAWE School",
               monthly_income=1500, emergency_contact_name="Marie Nshimiyimana", emergency_contact_phone="0784444444"),
    ]
    db.add_all(tenants)
    db.commit()

    # ── Leases ─────────────────────────────────────────────────────────────────
    now = datetime.utcnow()
    lease1 = Lease(property_id=props[0].id, tenant_id=tenants[0].id,
                   start_date=now - timedelta(days=180), end_date=now + timedelta(days=185),
                   rent_amount=500, deposit_amount=1000, deposit_paid=True,
                   status=LeaseStatus.active, payment_due_day=1, late_fee=25)
    lease2 = Lease(property_id=props[1].id, tenant_id=tenants[1].id,
                   start_date=now - timedelta(days=90), end_date=now + timedelta(days=275),
                   rent_amount=900, deposit_amount=1800, deposit_paid=True,
                   status=LeaseStatus.active, payment_due_day=5, late_fee=45)
    db.add_all([lease1, lease2])
    db.commit()

    # ── Payments ───────────────────────────────────────────────────────────────
    payments = []
    for i in range(1, 7):
        month = (now.month - i - 1) % 12 + 1
        year  = now.year if (now.month - i) > 0 else now.year - 1
        payments.append(Payment(
            lease_id=lease1.id, tenant_id=tenants[0].id,
            amount=500, amount_due=500, payment_method=PaymentMethod.bank_transfer,
            status=PaymentStatus.paid, payment_date=now - timedelta(days=30*i),
            due_date=now - timedelta(days=30*i - 1), period_month=month, period_year=year,
            transaction_ref=f"TXN-A-{1000+i}",
        ))
    for i in range(1, 4):
        month = (now.month - i - 1) % 12 + 1
        year  = now.year if (now.month - i) > 0 else now.year - 1
        payments.append(Payment(
            lease_id=lease2.id, tenant_id=tenants[1].id,
            amount=900, amount_due=900, payment_method=PaymentMethod.mobile_money,
            status=PaymentStatus.paid, payment_date=now - timedelta(days=30*i),
            due_date=now - timedelta(days=30*i - 4), period_month=month, period_year=year,
            transaction_ref=f"TXN-B-{2000+i}",
        ))
    # Add one pending payment for current month
    payments.append(Payment(
        lease_id=lease1.id, tenant_id=tenants[0].id,
        amount=0, amount_due=500, payment_method=PaymentMethod.bank_transfer,
        status=PaymentStatus.pending, due_date=now + timedelta(days=2),
        period_month=now.month, period_year=now.year,
    ))
    db.add_all(payments)
    db.commit()

    # ── Maintenance ────────────────────────────────────────────────────────────
    requests = [
        MaintenanceRequest(property_id=props[0].id, tenant_id=tenants[0].id,
                           title="Leaking tap in bathroom", description="The bathroom tap has been leaking for 3 days.",
                           priority=MaintenancePriority.medium, status=MaintenanceStatus.open,
                           estimated_cost=50),
        MaintenanceRequest(property_id=props[1].id, tenant_id=tenants[1].id,
                           title="Broken window latch", description="Kitchen window latch is broken, security risk.",
                           priority=MaintenancePriority.high, status=MaintenanceStatus.in_progress,
                           assigned_to="HandyFix Ltd", estimated_cost=80, actual_cost=75,
                           scheduled_date=now + timedelta(days=2)),
        MaintenanceRequest(property_id=props[0].id,
                           title="Annual plumbing inspection", description="Scheduled annual check of all plumbing.",
                           priority=MaintenancePriority.low, status=MaintenanceStatus.resolved,
                           assigned_to="PipePro Services", estimated_cost=150, actual_cost=140,
                           scheduled_date=now - timedelta(days=30), resolved_date=now - timedelta(days=28)),
    ]
    db.add_all(requests)
    db.commit()

    # ── Expenses ───────────────────────────────────────────────────────────────
    expenses = [
        Expense(property_id=props[0].id, category="Repair", amount=140,
                description="Plumbing inspection", vendor="PipePro Services", date=now - timedelta(days=28)),
        Expense(property_id=props[1].id, category="Insurance", amount=600,
                description="Annual building insurance", vendor="SafeGuard Insurance", date=now - timedelta(days=60)),
        Expense(property_id=props[0].id, category="Utilities", amount=80,
                description="Water bill Q1", vendor="WASAC", date=now - timedelta(days=45)),
        Expense(category="Tax", amount=1200, description="Annual property tax", date=now - timedelta(days=90)),
        Expense(property_id=props[1].id, category="Repair", amount=75,
                description="Window latch fix", vendor="HandyFix Ltd", date=now - timedelta(days=5)),
    ]
    db.add_all(expenses)
    db.commit()

    print("✅ Seed data created successfully!")
    print("─" * 40)
    print("Login credentials:")
    print("  Admin:      admin@rental.com      / admin123")
    print("  Manager:    manager@rental.com    / manager123")
    print("  Accountant: accountant@rental.com / accountant123")
    print("─" * 40)
    print("API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    seed()
    db.close()
