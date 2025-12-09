from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize Firebase BEFORE routers load
import firebase_init

# Import routers
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
)

# IMPORTANT: Disable slash redirects
app = FastAPI(
    title="Farm Management System API",
    version="1.0.0",
    redirect_slashes=False  # <── FIXES 307 REDIRECT ISSUE
)

# -----------------------------------------------------------
# CORS CONFIGURATION
# -----------------------------------------------------------

ALLOWED_ORIGINS = [
    # Local development
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",

    # Production frontend
    "https://farmxpat.com",
    "https://www.farmxpat.com",

    # Railway backend domain
    "https://farm-xpat-production.up.railway.app",
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
