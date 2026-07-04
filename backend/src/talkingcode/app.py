# noqa: import-boundary:fastapi-location,import-boundary:layer-no-internal-imports
"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from talkingcode.dependencies import _get_cached_config
from talkingcode.error_handlers import app_error_handler
from talkingcode.errors import AppError
from talkingcode.routes import chat_routes, health_routes, model_routes, repo_routes
from talkingcode.startup import (
    setup_database,
    setup_openai_agents_tracing,
    setup_telemetry_if_enabled,
)

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    config = _get_cached_config()
    setup_telemetry_if_enabled(config)
    setup_openai_agents_tracing()
    await setup_database(config)
    logger.info("Application started", environment=config.environment)
    yield
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="TalkingCode API",
        version="0.1.0",
        lifespan=lifespan,
    )
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore
    app.include_router(chat_routes.router, prefix="/chat", tags=["chat"])
    app.include_router(repo_routes.router, tags=["repos"])
    app.include_router(model_routes.router, tags=["models"])
    app.include_router(health_routes.router)
    return app


app = create_app()
