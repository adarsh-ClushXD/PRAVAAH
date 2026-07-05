"""
PRAVAAH Backend — FastAPI Application Entry Point.

This module wires together all application components:
  - Lifespan context (startup/shutdown)
  - API router registration
  - CORS middleware
  - Global exception handlers
  - OpenAPI documentation metadata
"""
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import get_settings
from app.database import initialize_database

settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Application lifespan manager.

    Startup: Initialize database tables, verify AI provider connectivity.
    Shutdown: Release resources gracefully.
    """
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env} | AI Provider: {settings.ai_provider}")

    # Initialize database schema
    await initialize_database()

    # Verify AI provider is reachable
    from app.ai.provider_factory import get_ai_provider
    provider = get_ai_provider()
    is_healthy = await provider.health_check()
    if is_healthy:
        logger.info(f"AI provider '{settings.ai_provider}' is healthy and ready.")
    else:
        logger.warning(
            f"AI provider '{settings.ai_provider}' health check failed. "
            "Analysis endpoints will return degraded responses."
        )

    # Start Background Scheduler
    from app.services.scheduler import scheduler
    scheduler.start()

    yield

    # Shutdown cleanup
    logger.info(f"Shutting down {settings.app_name}...")
    await scheduler.stop()
    from app.database import engine
    await engine.dispose()
    logger.info("Database connections released. Goodbye.")


def create_application() -> FastAPI:
    """
    Application factory.

    Constructs the FastAPI application with all middleware, routers,
    and exception handlers configured.
    """
    application = FastAPI(
        title=settings.app_name,
        description=(
            "Predictive River and Atmospheric Vulnerability Analysis "
            "for Adaptive Hazard Management — AI-powered flood intelligence "
            "platform for West Bengal."
        ),
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS Middleware ────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Analysis-ID"],
    )

    # ── Global Exception Handlers ──────────────────────────────────────────────
    @application.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(f"Unhandled exception on {request.url}: {exc!r}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please try again.",
                "path": str(request.url),
            },
        )

    # ── API Routers ────────────────────────────────────────────────────────────
    from app.api.routes import analysis, districts, weather, rivers, reports

    API_PREFIX = "/api/v1"

    application.include_router(
        districts.router, prefix=API_PREFIX, tags=["Districts"]
    )
    application.include_router(
        weather.router, prefix=API_PREFIX, tags=["Weather"]
    )
    application.include_router(
        rivers.router, prefix=API_PREFIX, tags=["Rivers"]
    )
    application.include_router(
        analysis.router, prefix=API_PREFIX, tags=["Analysis"]
    )
    application.include_router(
        reports.router, prefix=API_PREFIX, tags=["Reports"]
    )

    # ── Root Health Endpoint ───────────────────────────────────────────────────
    @application.get("/api/v1/health", tags=["System"])
    async def health_check() -> dict[str, Any]:
        """System health check — returns provider status and version."""
        from app.ai.provider_factory import get_ai_provider
        provider = get_ai_provider()
        provider_healthy = await provider.health_check()

        return {
            "status": "healthy" if provider_healthy else "degraded",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "ai_provider": settings.ai_provider,
            "ai_provider_healthy": provider_healthy,
        }

    return application


app = create_application()
