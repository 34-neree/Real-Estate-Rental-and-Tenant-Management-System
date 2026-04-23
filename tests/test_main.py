"""
Tests – run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test_rental.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helpers ────────────────────────────────────────────────────────────────────

def register_and_login(client, email="test@test.com", password="pass123", role="admin"):
    client.post("/api/auth/register", json={
        "full_name": "Test User", "email": email, "password": password, "role": role
    })
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ─────────────────────────────────────────────────────────────────

def test_register(client):
    r = client.post("/api/auth/register", json={
        "full_name": "Alice", "email": "alice@test.com", "password": "secret123", "role": "admin"
    })
    assert r.status_code == 201
    assert r.json()["email"] == "alice@test.com"


def test_login(client):
    client.post("/api/auth/register", json={
        "full_name": "Bob", "email": "bob@test.com", "password": "secret123", "role": "admin"
    })
    r = client.post("/api/auth/login", data={"username": "bob@test.com", "password": "secret123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_bad_credentials(client):
    r = client.post("/api/auth/login", data={"username": "nobody@test.com", "password": "wrong"})
    assert r.status_code == 401


# ── Property Tests ─────────────────────────────────────────────────────────────

def test_create_and_list_properties(client):
    token = register_and_login(client, "pm@test.com", "pass123", "admin")
    h = auth_headers(token)

    r = client.post("/api/properties/", json={
        "name": "Test Apartment", "address": "1 Main St", "city": "Kigali",
        "property_type": "apartment", "rent_amount": 500, "deposit_amount": 1000,
        "bedrooms": 2, "bathrooms": 1.0,
    }, headers=h)
    assert r.status_code == 201
    prop_id = r.json()["id"]

    r = client.get("/api/properties/", headers=h)
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()]
    assert prop_id in ids


def test_get_property(client):
    token = register_and_login(client, "pm2@test.com", "pass123", "admin")
    h = auth_headers(token)
    r = client.post("/api/properties/", json={
        "name": "Studio X", "address": "2 Side St", "city": "Kigali",
        "property_type": "studio", "rent_amount": 300, "deposit_amount": 600,
        "bedrooms": 1, "bathrooms": 1.0,
    }, headers=h)
    pid = r.json()["id"]
    r2 = client.get(f"/api/properties/{pid}", headers=h)
    assert r2.status_code == 200
    assert r2.json()["name"] == "Studio X"


# ── Tenant Tests ───────────────────────────────────────────────────────────────

def test_create_and_get_tenant(client):
    token = register_and_login(client, "mgr@test.com", "pass123", "admin")
    h = auth_headers(token)

    r = client.post("/api/tenants/", json={
        "first_name": "Eve", "last_name": "Doe", "email": "eve@test.com",
        "phone": "0780001234",
    }, headers=h)
    assert r.status_code == 201
    tid = r.json()["id"]

    r2 = client.get(f"/api/tenants/{tid}", headers=h)
    assert r2.status_code == 200
    assert r2.json()["first_name"] == "Eve"


# ── Payment Tests ──────────────────────────────────────────────────────────────

def test_overdue_payments_endpoint(client):
    token = register_and_login(client, "acc@test.com", "pass123", "admin")
    h = auth_headers(token)
    r = client.get("/api/payments/overdue", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Report Tests ───────────────────────────────────────────────────────────────

def test_dashboard(client):
    token = register_and_login(client, "dash@test.com", "pass123", "admin")
    h = auth_headers(token)
    r = client.get("/api/reports/dashboard", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_properties" in data
    assert "occupancy_rate" in data
    assert "monthly_income" in data


def test_income_report(client):
    token = register_and_login(client, "inc@test.com", "pass123", "admin")
    h = auth_headers(token)
    r = client.get("/api/reports/income?year=2025", headers=h)
    assert r.status_code == 200
    assert "annual_total" in r.json()


# ── Maintenance Tests ──────────────────────────────────────────────────────────

def test_maintenance_request(client):
    token = register_and_login(client, "maint@test.com", "pass123", "admin")
    h = auth_headers(token)

    prop = client.post("/api/properties/", json={
        "name": "Maint Prop", "address": "9 Fix St", "city": "Kigali",
        "property_type": "apartment", "rent_amount": 400, "deposit_amount": 800,
        "bedrooms": 1, "bathrooms": 1.0,
    }, headers=h).json()

    r = client.post("/api/maintenance/", json={
        "property_id": prop["id"], "title": "Broken Door",
        "description": "Front door lock broken", "priority": "high",
    }, headers=h)
    assert r.status_code == 201
    assert r.json()["status"] == "open"
