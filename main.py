from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scheduler import start_scheduler

import firebase_init

# DB setup
from database import engine
from models import Base

# Start background scheduler
start_scheduler()

# -----------------------------------------------------------
# CREATE DATABASE TABLES
# -----------------------------------------------------------
Base.metadata.create_all(bind=engine)

# -----------------------------------------------------------
# IMPORT ROUTERS
# -----------------------------------------------------------
from routers import (
    auth,
    livestock,
    crops,
    inventory,
    finance,
    workers,
    notifications,
    reports,
    dashboard,
    assistant,
    marketplace,
    marketplace_chat,
    marketplace_ws,
    admin_analytics,
)

# -----------------------------------------------------------
# APP INIT
# -----------------------------------------------------------
app = FastAPI(
    title="Farm Management System API",
    version="1.0.0",
    redirect_slashes=False
)

# -----------------------------------------------------------
# CORS CONFIGURATION
# -----------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "https://farmxpat.com",
    "https://www.farmxpat.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# -----------------------------------------------------------
# ROUTERS
# -----------------------------------------------------------
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(livestock.router, prefix="/api/livestock", tags=["livestock"])
app.include_router(crops.router, prefix="/api/crops", tags=["crops"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(finance.router, prefix="/api/finance", tags=["finance"])
app.include_router(workers.router, prefix="/api/workers", tags=["workers"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["assistant"])
app.include_router(marketplace_chat.router, prefix="/api/marketplace", tags=["marketplace-chat"])
app.include_router(marketplace.router, prefix="/api/marketplace", tags=["marketplace"])
app.include_router(admin_analytics.router, prefix="/api/admin/analytics", tags=["admin-analytics"])

app.include_router(marketplace_ws.router, prefix="/api", tags=["marketplace-ws"])

# -----------------------------------------------------------
# ROOT + HEALTH ENDPOINTS
# -----------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "Farm Management API is running",
        "version": "1.0.0",
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}