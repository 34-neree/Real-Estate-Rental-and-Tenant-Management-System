# 🏢 Real Estate Rental & Tenant Management System

A full-featured REST API built with **FastAPI**, **SQLAlchemy**, and **SQLite/PostgreSQL** for managing rental properties, tenants, leases, payments, and maintenance — complete with a dark-themed Jinja2 frontend dashboard.

---

## 📋 What This App Does

This application is a **complete rental property management platform** designed for landlords, property managers, and real estate agencies. It streamlines every aspect of day-to-day rental operations through a RESTful API and an integrated web dashboard.

### Core Features

| Module | Description |
|--------|-------------|
| **🏠 Property Management** | Create, update, and track rental properties with details like address, type, rent amount, and availability status. Filter and search across your entire portfolio. |
| **👤 Tenant Management** | Maintain a tenant directory with contact info, search capabilities, and per-tenant balance overviews (total owed, paid, and outstanding). |
| **📄 Lease Management** | Create and manage lease agreements linking tenants to properties. Includes lease renewal, expiry alerts, date validation, and double-booking prevention. |
| **💳 Payment Tracking** | Record rent payments, auto-detect overdue payments, and view tenant payment histories with summaries of amounts paid and outstanding. |
| **🔧 Maintenance Requests** | Tenants can submit maintenance requests with priority levels; managers can track, update, and resolve them. |
| **💰 Expense Tracking** | Log property-related expenses (repairs, insurance, utilities, etc.) categorized for reporting. |
| **📊 Reports & Analytics** | Dashboard with KPIs, monthly income/expense charts, occupancy rates, profit/loss reports, tenant arrears lists, and lease expiry alerts. |
| **🔐 Authentication & RBAC** | JWT-based login with four roles — **Admin**, **Manager**, **Accountant**, and **Tenant** — each with fine-grained permissions. |
| **🔔 Notifications** | In-app notification system for important events (overdue payments, lease expirations, etc.). |


---

## 📦 Project Structure

```
rental_system/
├── app/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Settings (env vars)
│   ├── database.py           # DB engine & session
│   ├── models/
│   │   └── models.py         # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py        # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py           # Register & login
│   │   ├── users.py          # User management
│   │   ├── properties.py     # Property CRUD + filtering
│   │   ├── tenants.py        # Tenant CRUD + search
│   │   ├── leases.py         # Lease management + expiry alerts
│   │   ├── payments.py       # Payment tracking + overdue
│   │   ├── maintenance.py    # Maintenance requests
│   │   ├── expenses.py       # Expense tracking
│   │   └── reports.py        # Analytics & dashboards
│   └── utils/
│       └── auth.py           # JWT + password hashing + RBAC
├── alembic/                  # Database migrations
├── tests/
│   └── test_main.py          # Pytest test suite
├── seed.py                   # Demo data loader
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Quick Start

### 1. Clone & Set Up Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env as needed (SQLite works out of the box)
```

### 2. Run the Server

```bash
uvicorn app.main:app --reload
```

API will be live at: **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

### 3. Load Demo Data (Optional)

```bash
python seed.py
```

This creates sample properties, tenants, leases, payments, and maintenance requests.

**Demo login credentials:**
| Role       | Email                    | Password       |
|------------|--------------------------|----------------|
| Admin      | admin@rental.com         | admin123       |
| Manager    | manager@rental.com       | manager123     |
| Accountant | accountant@rental.com    | accountant123  |

---

## 🐳 Docker Setup

```bash
# Copy and configure env
cp .env.example .env
# Update DATABASE_URL to use PostgreSQL (see .env.example)

# Start all services
docker-compose up --build
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🔐 Authentication

The API uses **JWT Bearer tokens**.

1. Register: `POST /api/auth/register`
2. Login: `POST /api/auth/login` → returns `access_token`
3. Use in requests: `Authorization: Bearer <token>`

---

## 👥 User Roles & Permissions

| Feature              | Admin | Manager | Accountant | Tenant |
|----------------------|-------|---------|------------|--------|
| Manage properties    | ✅    | ✅      | ❌         | ❌     |
| Manage tenants       | ✅    | ✅      | ❌         | ❌     |
| Manage leases        | ✅    | ✅      | ❌         | View   |
| Record payments      | ✅    | ✅      | ✅         | ❌     |
| View reports         | ✅    | ✅      | ✅         | ❌     |
| Maintenance requests | ✅    | ✅      | ❌         | ✅     |
| Manage expenses      | ✅    | ✅      | ✅         | ❌     |
| Manage users         | ✅    | ❌      | ❌         | ❌     |

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint              | Description         |
|--------|-----------------------|---------------------|
| POST   | /api/auth/register    | Register new user   |
| POST   | /api/auth/login       | Login & get token   |

### Properties
| Method | Endpoint                    | Description             |
|--------|-----------------------------|-------------------------|
| GET    | /api/properties/            | List all (with filters) |
| GET    | /api/properties/available   | Available only          |
| POST   | /api/properties/            | Create property         |
| GET    | /api/properties/{id}        | Get by ID               |
| PUT    | /api/properties/{id}        | Update property         |
| DELETE | /api/properties/{id}        | Delete property         |

### Tenants
| Method | Endpoint               | Description              |
|--------|------------------------|--------------------------|
| GET    | /api/tenants/          | List (search, filter)    |
| POST   | /api/tenants/          | Create tenant            |
| GET    | /api/tenants/{id}      | Get by ID                |
| PUT    | /api/tenants/{id}      | Update tenant            |
| DELETE | /api/tenants/{id}      | Delete tenant            |

### Leases
| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| GET    | /api/leases/                  | List (filter by status)  |
| GET    | /api/leases/expiring-soon     | Expiring within N days   |
| POST   | /api/leases/                  | Create lease             |
| GET    | /api/leases/{id}              | Get by ID                |
| PUT    | /api/leases/{id}              | Update / terminate       |
| DELETE | /api/leases/{id}              | Delete lease             |

### Payments
| Method | Endpoint                 | Description              |
|--------|--------------------------|--------------------------|
| GET    | /api/payments/           | List (filter by status)  |
| GET    | /api/payments/overdue    | All overdue payments     |
| POST   | /api/payments/           | Record payment           |
| PUT    | /api/payments/{id}       | Mark as paid / update    |
| DELETE | /api/payments/{id}       | Delete payment           |

### Maintenance
| Method | Endpoint                  | Description              |
|--------|---------------------------|--------------------------|
| GET    | /api/maintenance/         | List (filter/priority)   |
| POST   | /api/maintenance/         | Submit request           |
| GET    | /api/maintenance/{id}     | Get by ID                |
| PUT    | /api/maintenance/{id}     | Update / resolve         |
| DELETE | /api/maintenance/{id}     | Delete request           |

### Reports & Analytics
| Method | Endpoint                        | Description              |
|--------|---------------------------------|--------------------------|
| GET    | /api/reports/dashboard          | KPI summary              |
| GET    | /api/reports/income             | Monthly income by year   |
| GET    | /api/reports/expenses           | Expenses by category     |
| GET    | /api/reports/occupancy          | Per-property occupancy   |
| GET    | /api/reports/leases/expiring    | Expiring lease alerts    |
| GET    | /api/reports/payments/summary   | Monthly payment summary  |

### Expenses
| Method | Endpoint               | Description              |
|--------|------------------------|--------------------------|
| GET    | /api/expenses/         | List expenses            |
| POST   | /api/expenses/         | Add expense              |
| GET    | /api/expenses/{id}     | Get by ID                |
| DELETE | /api/expenses/{id}     | Delete expense           |

---

## 🗄️ Database Migrations (Alembic)

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "describe change"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

---

## ⚙️ Switching to PostgreSQL

1. Install driver: `pip install psycopg2-binary`
2. Update `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/rental_db
   ```
3. Remove `connect_args` from `database.py` (already handled conditionally)

---

## 🛠️ Tech Stack

| Layer        | Technology                    |
|--------------|-------------------------------|
| Language     | Python 3.11+                  |
| Framework    | FastAPI                       |
| ORM          | SQLAlchemy 2.0                |
| Validation   | Pydantic v2                   |
| Auth         | JWT (python-jose) + bcrypt    |
| DB (dev)     | SQLite                        |
| DB (prod)    | PostgreSQL                    |
| Migrations   | Alembic                       |
| Testing      | Pytest + HTTPX                |
| Deployment   | Docker + Docker Compose       |
