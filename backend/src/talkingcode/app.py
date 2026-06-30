"""FastAPI app factory and error handlers."""
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator

import mlflow
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy import text

from talkingcode.dependencies import _get_cached_config
from talkingcode.errors import AppError, InfraError, NotFoundError
from talkingcode.repository.database import get_engine
from talkingcode.telemetry import configure_telemetry

if TYPE_CHECKING:
    from talkingcode.config import AppConfig

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)
_mlflow_autolog_enabled = False


def configure_mlflow_tracing() -> None:
    """Enable MLflow tracing after environment configuration is loaded."""
    global _mlflow_autolog_enabled
    if _mlflow_autolog_enabled:
        return

    mlflow.autolog()
    _mlflow_autolog_enabled = True
    logger.info(
        "mlflow.tracing.enabled",
        tracking_uri=os.getenv("MLFLOW_TRACKING_URI", ""),
    )


async def setup_database(config: "AppConfig") -> None:
    """Verify database connectivity without mutating schema."""
    engine = get_engine(config.database_url)
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    await engine.dispose()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup — use cached config to avoid redundant Infisical calls
    config = _get_cached_config()
    configure_mlflow_tracing()

    # Telemetry
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    service_name = os.getenv("OTEL_SERVICE_NAME", "talkingcode-backend")
    otel_env = os.getenv("OTEL_ENVIRONMENT", config.environment)
    if endpoint:
        configure_telemetry(endpoint=endpoint, service_name=service_name, environment=otel_env)
        logger.info("telemetry.enabled", endpoint=endpoint, service_name=service_name)
    else:
        logger.info("telemetry.disabled")

    await setup_database(config)
    logger.info("Application started", environment=config.environment)

    yield

    # Shutdown
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="TalkingCode API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    # Instrument HTTPX
    HTTPXClientInstrumentor().instrument()

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Error handlers
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        status_code = 400
        error_code = "unknown_error"
        message = str(exc)
        
        if isinstance(exc, NotFoundError):
            status_code = 404
            error_code = "not_found"
            message = f"{exc.resource} not found"
        elif isinstance(exc, InfraError):
            status_code = 502
            error_code = "infrastructure_error"
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": error_code,
                "message": message,
            },
        )
    
    # Include routers
    from talkingcode.routes import chat_routes, model_routes, repo_routes

    app.include_router(chat_routes.router, prefix="/chat", tags=["chat"])
    app.include_router(repo_routes.router, tags=["repos"])
    app.include_router(model_routes.router, tags=["models"])
    
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}
    
    return app


app = create_app()
