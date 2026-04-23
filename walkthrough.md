# Rental Management System — Upgrade Walkthrough

## Summary
Upgraded the FastAPI backend with missing business logic and added a complete dark brownish frontend dashboard served via Jinja2 templates.

---

## Backend Changes

### Models ([models.py](file:///c:/Users/USER/Downloads/rental_system/app/models/models.py))
- **Notification** model — in-app alerts with title, message, category, read status
- **AuditLog** model — tracks user actions (create, update, delete, login, renew)
- **AuditAction** enum — create, update, delete, login, renew, status_change
- **Lease.renewed_from_id** — links renewed leases to their originals

### Schemas ([schemas.py](file:///c:/Users/USER/Downloads/rental_system/app/schemas/schemas.py))
- `LoginResponse` — returns user info alongside JWT token
- `PasswordChange` — with min-length validator
- `LeaseRenew` — for lease renewal with date validation
- `LeaseCreate` — added end_date > start_date validator
- `ExpenseUpdate` — was completely missing
- `TenantBalanceOut` — financial overview per tenant
- `TenantPaymentSummary` — payment aggregates per tenant
- `NotificationOut`, `AuditLogOut` — output schemas for new models

### Routers

| Router | New Endpoints | Key Improvements |
|--------|--------------|-----------------|
| [auth.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/auth.py) | — | Returns user info on login, audit logging, inactive account check |
| [users.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/users.py) | `PUT /me/password` | Password change, self-deletion prevention, role-change guard |
| [leases.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/leases.py) | `POST /{id}/renew` | Tenant/property validation, double-booking prevention, audit logs |
| [payments.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/payments.py) | `PUT /mark-overdue`, `GET /tenant/{id}/summary` | Lease/tenant validation, batch overdue marking |
| [tenants.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/tenants.py) | `GET /{id}/balance` | Balance overview (total due/paid/outstanding/overdue) |
| [expenses.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/expenses.py) | `PUT /{id}` | Update endpoint was missing |
| [reports.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/reports.py) | `GET /profit-loss`, `GET /arrears` | Monthly P&L, tenant arrears list, expenses in dashboard |
| [notifications.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/notifications.py) | Full CRUD | List, unread count, mark read, mark all read |

### Other Backend
- [config.py](file:///c:/Users/USER/Downloads/rental_system/app/config.py) — `FRONTEND_ENABLED`, `DEFAULT_ADMIN_EMAIL/PASSWORD`
- [main.py](file:///c:/Users/USER/Downloads/rental_system/app/main.py) — Static files, Jinja2 templates, health check (`/health`), admin bootstrap on startup
- [requirements.txt](file:///c:/Users/USER/Downloads/rental_system/requirements.txt) — Added `jinja2`, `aiofiles`

---

## Frontend (Dark Brownish Aesthetic)

### Design System ([style.css](file:///c:/Users/USER/Downloads/rental_system/static/css/style.css))
- **Palette**: Deep espresso `#0d0907`, mocha `#1a120b`, caramel accent `#d5a574`, cream text `#e5e5cb`
- Glassmorphism cards with `backdrop-filter: blur(20px)`
- Gradient accent buttons and KPI card top-borders
- Smooth transitions on all interactive elements
- Google Font "Inter" typography
- Responsive sidebar that collapses on mobile
- Toast notification system, modals, status badges, loading spinners

### JavaScript
- [auth.js](file:///c:/Users/USER/Downloads/rental_system/static/js/auth.js) — Login/logout, JWT token management in localStorage
- [app.js](file:///c:/Users/USER/Downloads/rental_system/static/js/app.js) — API wrapper, CRUD for all entities, toast system, sidebar toggle
- [charts.js](file:///c:/Users/USER/Downloads/rental_system/static/js/charts.js) — Lightweight CSS bar chart renderer

### Pages (10 Jinja2 templates)
| Page | File |
|------|------|
| Login | [login.html](file:///c:/Users/USER/Downloads/rental_system/templates/login.html) |
| Dashboard | [dashboard.html](file:///c:/Users/USER/Downloads/rental_system/templates/dashboard.html) |
| Properties | [properties.html](file:///c:/Users/USER/Downloads/rental_system/templates/properties.html) |
| Tenants | [tenants.html](file:///c:/Users/USER/Downloads/rental_system/templates/tenants.html) |
| Leases | [leases.html](file:///c:/Users/USER/Downloads/rental_system/templates/leases.html) |
| Payments | [payments.html](file:///c:/Users/USER/Downloads/rental_system/templates/payments.html) |
| Maintenance | [maintenance.html](file:///c:/Users/USER/Downloads/rental_system/templates/maintenance.html) |
| Expenses | [expenses.html](file:///c:/Users/USER/Downloads/rental_system/templates/expenses.html) |
| Reports | [reports.html](file:///c:/Users/USER/Downloads/rental_system/templates/reports.html) |
| Base Layout | [base.html](file:///c:/Users/USER/Downloads/rental_system/templates/base.html) |

---

## How to Run on Another PC

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload

# 4. Open browser
# Frontend: http://localhost:8000
# API docs: http://localhost:8000/docs
# Login:    admin@rental.com / admin123
```

> [!TIP]
> The admin user is auto-created on first startup if no users exist. You can also run `python seed.py` to load demo data.
