"""Sentinel AI — FastAPI Application Entrypoint."""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .core.exceptions import SentinelException
from .core.session_store import session_store
from .db.session import init_db
from .schemas.common import HealthResponse, ErrorResponse
from .api.v1.router import api_router

# Configure minimal, sanitized logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sentinel_ai")


async def session_ttl_cleaner():
    """Background task running every 5 minutes to prune expired in-memory sessions."""
    while True:
        try:
            await asyncio.sleep(300)
            pruned = session_store.cleanup_expired()
            if pruned > 0:
                logger.info(f"TTL Cleanup: Pruned {pruned} expired analysis session(s).")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error during TTL cleanup: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for background workers and database lifecycle."""
    logger.info("Initializing Sentinel AI Backend Services & Database...")
    try:
        await init_db()
        logger.info("Database schema verified.")
    except Exception as e:
        logger.warning(f"Database initialization warning: {str(e)}")

    cleaner_task = asyncio.create_task(session_ttl_cleaner())
    yield
    logger.info("Shutting down Sentinel AI Backend Services...")
    cleaner_task.cancel()
    try:
        await cleaner_task
    except asyncio.CancelledError:
        pass


def create_application() -> FastAPI:
    """Factory creating and configuring the production FastAPI instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="AI-Powered Fraud Detection & Risk Intelligence Platform API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 1. Domain Exception Handler
    @app.exception_handler(SentinelException)
    async def domain_exception_handler(request: Request, exc: SentinelException):
        logger.warning(f"Sentinel Domain Exception [{exc.code}]: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.code,
                "message": exc.message
            }
        )

    # 2. General Unhandled Exception Handler (No raw stack traces in production)
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred during processing. Please verify input data and try again."
            }
        )

    # Health Check Endpoint
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="Service Health Check"
    )
    async def health_check() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            service="sentinel-ai",
            version=settings.VERSION
        )

    # Mount v1 Router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
