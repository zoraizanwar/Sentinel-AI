"""Master v1 API Router for Sentinel AI."""
from fastapi import APIRouter

from .auth import router as auth_router
from .organizations import router as organizations_router
from .clients import router as clients_router
from .datasets import router as datasets_router
from .analyses import router as analyses_router
from .transactions import router as transactions_router
from .explain import router as explain_router
from .reports import router as reports_router
from .audit_logs import router as audit_logs_router
from .upload import router as upload_router
from .analyze import router as legacy_analyze_router

api_router = APIRouter()

# Authentication & Tenancy
api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(clients_router)
api_router.include_router(datasets_router)
api_router.include_router(analyses_router)
api_router.include_router(transactions_router)
api_router.include_router(explain_router)
api_router.include_router(reports_router)
api_router.include_router(audit_logs_router)

# Legacy Session Endpoints (Backward Compatibility)
api_router.include_router(upload_router, tags=["Dataset Ingestion & Validation"])
api_router.include_router(legacy_analyze_router, tags=["Fraud Analysis & Intelligence"])
