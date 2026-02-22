"""FastAPI app factory and error handlers."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from talkingcode.config import AppConfig
from talkingcode.errors import TalkingCodeError
from talkingcode.repository.database import get_engine, init_db

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


async def setup_database(config: AppConfig) -> None:
    """Initialize database tables."""
    engine = get_engine(config.database_url)
    await init_db(engine)
    await engine.dispose()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    config = AppConfig.from_env()
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
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Error handlers
    @app.exception_handler(TalkingCodeError)
    async def talkingcode_error_handler(request: Request, exc: TalkingCodeError) -> JSONResponse:
        status_code = 400
        if exc.code == "not_found":
            status_code = 404
        elif exc.code == "timeout":
            status_code = 504
        elif exc.code in ("llm_error", "planner_error"):
            status_code = 502
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )
    
    # Include routers
    from talkingcode.controllers import chat_controller
    app.include_router(chat_controller.router, prefix="/chat", tags=["chat"])
    
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}
    
    return app


app = create_app()
