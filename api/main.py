"""FastAPI application entry point for the Secure Document Management System.

Configures CORS, startup/shutdown lifecycle (MongoDB, storage), and
includes all route modules under the ``/api`` prefix.

Run with::

    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from database.manager import DatabaseManager
from exceptions.custom_exceptions import (
    SDMSException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    CryptographicError,
    DatabaseError,
    FileHandlingError,
)
from logger.logging_config import get_logger
from storage.manager import StorageManager

# Ensure the project root is on sys.path so that existing modules
# (services, models, crypto, etc.) can be imported without modification.
_project_root: Path = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

logger = get_logger(__name__)

# ------------------------------------------------------------------
# Application factory
# ------------------------------------------------------------------

app = FastAPI(
    title="Secure Document Management System API",
    description=(
        "REST API wrapping the SDMS hybrid-encryption document "
        "management backend with JWT authentication."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ------------------------------------------------------------------
# CORS — allow all origins in development
# ------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Exception handlers
# ------------------------------------------------------------------


_EXCEPTION_STATUS_MAP: dict[type, int] = {
    AuthenticationError: 401,
    AuthorizationError: 403,
    ValidationError: 422,
    FileHandlingError: 400,
    CryptographicError: 500,
    DatabaseError: 503,
}


@app.exception_handler(SDMSException)
async def sdms_exception_handler(request: Request, exc: SDMSException) -> JSONResponse:
    logger.error("SDMS exception: %s", exc)
    status_code = _EXCEPTION_STATUS_MAP.get(type(exc), 500)
    for exc_type, code in _EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            status_code = code
            break
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unexpected error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "detail": "Internal server error."},
    )

# ------------------------------------------------------------------
# Startup / Shutdown
# ------------------------------------------------------------------


@app.on_event("startup")
def on_startup() -> None:
    """Connect to MongoDB, create indexes, initialise storage dirs."""
    logger.info("Starting SDMS API ...")
    db_mgr = DatabaseManager()
    db_mgr.connect()
    db_mgr.create_indexes()
    logger.info("Database ready.")

    storage_mgr = StorageManager()
    storage_mgr.initialise()
    logger.info("Storage ready.")

    logger.info("SDMS API started. Environment: %s", settings.APP_ENVIRONMENT)


@app.on_event("shutdown")
def on_shutdown() -> None:
    """Close the MongoDB connection pool."""
    logger.info("Shutting down SDMS API ...")
    DatabaseManager().disconnect()
    logger.info("SDMS API stopped.")


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok"}


# ------------------------------------------------------------------
# Register routers
# ------------------------------------------------------------------

from api.routes.auth import router as auth_router
from api.routes.audit import router as audit_router
from api.routes.documents import router as documents_router
from api.routes.stats import router as stats_router
from api.routes.users import router as users_router

app.include_router(auth_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
