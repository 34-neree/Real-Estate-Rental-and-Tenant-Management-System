# Rental Management System — Professional Upgrade

Upgrade the FastAPI backend with missing business logic, better validation, and professional patterns; then add a dark brownish aesthetic frontend dashboard served directly via Jinja2 templates from FastAPI (no separate frontend server needed).

---

## Proposed Changes

### 1. Backend — Missing & Enhanced Functionality

#### [MODIFY] [leases.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/leases.py)
- **Lease renewal endpoint** — `POST /api/leases/{id}/renew` creates a new lease linked to the same property/tenant, adjusting dates
- **Validate tenant exists** before creating lease
- **Validate date logic** (end_date > start_date)
- **Prevent double-booking** — reject if tenant already has an active lease on the same property

#### [MODIFY] [payments.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/payments.py)
- **Auto-mark overdue** — `PUT /api/payments/mark-overdue` batch-marks pending payments past due_date
- **Tenant payment history** — `GET /api/payments/tenant/{tenant_id}/summary` returns total paid, outstanding, overdue count
- **Validate lease exists** and belongs to the tenant before recording payment

#### [MODIFY] [expenses.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/expenses.py)
- **Add `PUT` update** endpoint for expenses (currently missing)

#### [MODIFY] [tenants.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/tenants.py)
- **Tenant balance overview** — `GET /api/tenants/{id}/balance` returns total owed, paid, and outstanding across all leases

#### [MODIFY] [users.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/users.py)
- **Change password** — `PUT /api/users/me/password` for authenticated user to change their own password

#### [MODIFY] [auth.py (router)](file:///c:/Users/USER/Downloads/rental_system/app/routers/auth.py)
- Return **user info** (id, name, role) alongside the token on login for frontend session management

#### [MODIFY] [reports.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/reports.py)
- **Profit/Loss report** — `GET /api/reports/profit-loss` (income minus expenses by month)
- **Tenant arrears list** — `GET /api/reports/arrears` lists tenants with overdue balances

#### [MODIFY] [schemas.py](file:///c:/Users/USER/Downloads/rental_system/app/schemas/schemas.py)
- Add `ExpenseUpdate` schema
- Add `PasswordChange` schema
- Add `LeaseRenew` schema
- Add pagination wrapper `PaginatedResponse` generic schema
- Add `LoginResponse` schema (token + user info)

#### [MODIFY] [models.py](file:///c:/Users/USER/Downloads/rental_system/app/models/models.py)
- Add **AuditLog** model for tracking important actions (lease created, payment recorded, etc.)
- Add **Notification** model (title, message, user_id, read status, created_at) for in-app alerts

#### [NEW] [notifications.py](file:///c:/Users/USER/Downloads/rental_system/app/routers/notifications.py)
- `GET /api/notifications/` — list user's notifications
- `PUT /api/notifications/{id}/read` — mark as read
- `GET /api/notifications/unread-count` — count unread

#### [MODIFY] [main.py](file:///c:/Users/USER/Downloads/rental_system/app/main.py)
- Register notifications router
- Mount static files for frontend
- Add Jinja2 template rendering for frontend pages
- Add startup event to auto-create admin user if none exists
- Add health check endpoint `GET /health`

#### [MODIFY] [config.py](file:///c:/Users/USER/Downloads/rental_system/app/config.py)
- Add `FRONTEND_ENABLED` flag
- Add `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD` for first-run bootstrap

#### [MODIFY] [requirements.txt](file:///c:/Users/USER/Downloads/rental_system/requirements.txt)
- Add `jinja2` and `aiofiles` for template rendering and static file serving

---

### 2. Frontend — Dark Brownish Aesthetic Dashboard (Jinja2 + Vanilla JS)

All frontend files served by FastAPI — no separate frontend framework needed.

#### [NEW] [static/](file:///c:/Users/USER/Downloads/rental_system/static/) directory
- `css/style.css` — Full dark brownish design system with glassmorphism, gradients, and micro-animations
- `js/app.js` — Main application logic (API calls, DOM manipulation, SPA-like navigation)
- `js/auth.js` — Login/register form handling, token storage
- `js/charts.js` — Dashboard chart rendering (lightweight, no external library)

#### [NEW] [templates/](file:///c:/Users/USER/Downloads/rental_system/templates/) directory
- `base.html` — Base layout with sidebar navigation, header, dark brownish theme
- `login.html` — Login page with aesthetic form design
- `dashboard.html` — KPI cards, charts, recent activity
- `properties.html` — Property list with cards, filters, CRUD modals
- `tenants.html` — Tenant directory with search, detail panels
- `leases.html` — Lease management with status indicators
- `payments.html` — Payment tracking with overdue highlights
- `maintenance.html` — Request list with priority badges
- `expenses.html` — Expense log with category grouping
- `reports.html` — Analytics with income/expense charts

#### Design Aesthetic
- **Color Palette**: Deep espresso (#1a120b), warm mocha (#3c2a21), rich caramel (#d5cea3), cream accents (#e5e5cb)
- **Glassmorphism** cards with subtle backdrop blur
- **Smooth transitions** on all interactive elements
- **Google Font**: "Inter" for clean typography
- **Responsive** sidebar that collapses on mobile
- **Gradient accents** on buttons and headers
- **Status badges** with color-coded indicators

---

## Verification Plan

### Automated Tests
- Run `pytest tests/ -v` to confirm existing tests still pass
- Start server with `uvicorn app.main:app --reload` and verify all new endpoints via `/docs`
- Open browser to `http://localhost:8000` to verify frontend loads with dark brownish design

### Manual Verification
- Login flow works end-to-end from the UI
- Dashboard KPIs render correctly
- CRUD operations work from the frontend for all entities
- Responsive design works on narrow viewports
