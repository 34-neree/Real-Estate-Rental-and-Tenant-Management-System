from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import properties, tenants, leases, payments, maintenance, reports, auth, users, expenses
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Real Estate Rental & Tenant Management System",
    description="Comprehensive system for managing rental properties, tenants, leases, and payments.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/api/auth",        tags=["Authentication"])
app.include_router(users.router,       prefix="/api/users",       tags=["Users"])
app.include_router(properties.router,  prefix="/api/properties",  tags=["Properties"])
app.include_router(tenants.router,     prefix="/api/tenants",     tags=["Tenants"])
app.include_router(leases.router,      prefix="/api/leases",      tags=["Leases"])
app.include_router(payments.router,    prefix="/api/payments",    tags=["Payments"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["Maintenance"])
app.include_router(reports.router,     prefix="/api/reports",     tags=["Reports"])


app.include_router(expenses.router,    prefix="/api/expenses",    tags=["Expenses"])


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Rental Management System API", "docs": "/docs"}
