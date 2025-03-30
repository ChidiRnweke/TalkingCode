import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from typing import AsyncGenerator, AsyncIterator, TypedDict, cast

import numpy as np
import structlog
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.backend.config import AppConfig, configure_telemetry
from talkingcode.backend.errors import (
    AppError,
    InfraError,
    InputError,
    MaximumSpendError,
    TokenLimitError,
)
from talkingcode.backend.rag import (
    InputQuery,
    KeywordIdentifier,
    KeywordIdentifierService,
    OpenAIEmbeddingService,
    OpenAIGenerationService,
    RemainingSpend,
    RetrievalAugmentedGeneration,
    RetrievalService,
    SQLTokenStore,
    vector_store_from_config,
)
from talkingcode.backend.rag.retrieve import EmbeddedChunk
from talkingcode.pipelines.config import IngestionConfig

logger: structlog.stdlib.BoundLogger = structlog.getLogger("talkingcode")


router = APIRouter()


class State(TypedDict):
    app_config: AppConfig
    retrieval_service: RetrievalService
    ingestion_config: IngestionConfig


@dataclass(frozen=True, slots=True)
class HealthResponse:
    status: str
    remaining_spend: float


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    """
    This function is used to manage the lifespan of the FastAPI application.
    It is used to set up the application configuration and store it as a singleton.
    This singleton is then used to provide configuration to the application's dependencies.
    The configuration contains the database session, OpenAI client, and other configuration values.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    config = AppConfig.from_config()
    retrieval_service = vector_store_from_config(config)
    ingestion_config = IngestionConfig.from_env()
    yield {
        "app_config": config,
        "retrieval_service": retrieval_service,
        "ingestion_config": ingestion_config,
    }


async def get_database_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    This function is used to get an async session from the application configuration.
    It draws the session from the application configuration and yields it to the caller.
    This way we are certain that a new session is created for each request.

    Returns:
        AsyncGenerator[AsyncSession, None]: The async session generator.

    Yields:
        (Iterator[AsyncGenerator[AsyncSession, None]]): The async session generator.
    """
    config = cast(AppConfig, request.state.app_config)
    async with config.async_session() as session:
        yield session


async def get_retrieval_service(request: Request) -> RetrievalService:
    """
    This function is used to get the retrieval service from the application configuration.
    It returns the retrieval service from the application configuration.

    Returns:
        (RetrievalService): The retrieval service.
    """
    retrieval_service = cast(RetrievalService, request.state.retrieval_service)
    return retrieval_service


def get_app_config(request: Request) -> AppConfig:
    config = cast(AppConfig, request.state.app_config)
    return config


def get_keyword_identifier(config: AppConfig) -> KeywordIdentifier:
    return KeywordIdentifierService(
        client=config.openAI_client,
        model_name=config.keyword_identifier_model,
        prompt=config.keyword_identifier_prompt,
    )


@router.post("/rag/chat")
async def chat(
    question: InputQuery,
    session: AsyncSession = Depends(get_database_session),
    app_config: AppConfig = Depends(get_app_config),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> StreamingResponse:
    """
    This function is used to handle the chat endpoint. It is used to handle the incoming
    chat requests and generate the response using the RAG model. The RAG model is used to
    retrieve the context, embed the text, and generate the response. The response is then
    returned to the user.

    Args:
        question (InputQuery): The input query object.
        session (AsyncSession): The async session object. This is provided by the FastAPI
            dependency injection.
    """
    keyword_identifier = get_keyword_identifier(app_config)
    token_store = SQLTokenStore(async_session=session)
    openai_embedding_service = OpenAIEmbeddingService(
        client=app_config.openAI_client,
        embedding_model=app_config.embedding_model,
        token_store=token_store,
    )
    openai_generation_service = OpenAIGenerationService(
        client=app_config.openAI_client,
        model=app_config.chat_model,
        system_prompt=app_config.system_prompt,
        token_store=token_store,
    )

    rag = RetrievalAugmentedGeneration(
        embedding_service=openai_embedding_service,
        generation_service=openai_generation_service,
        retrieval_service=retrieval_service,
        max_spend=app_config.max_spend,
        token_store=token_store,
        keyword_identification_service=keyword_identifier,
        date=date.today(),
    )

    async def event_generator():
        chunk_stream = rag.rag_stream(question)
        async for chunk in chunk_stream:
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/rag/remaining_spend", response_model=RemainingSpend)
async def remaining_spend(
    session: AsyncSession = Depends(get_database_session),
    app_config: AppConfig = Depends(get_app_config),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> RemainingSpend:
    """
    This function is used to get the remaining spend for the day. It is used to get the
    remaining spend for the day by querying the database and calculating the remaining
    spend based on the maximum spend for the day.

    Args:
        session (AsyncSession): The async session object. This is provided by the FastAPI
            dependency injection.

    Returns:
        (RemainingSpend): The remaining spend object containing the remaining spend for
            the day.
    """
    keyword_identifier = get_keyword_identifier(app_config)
    token_store = SQLTokenStore(async_session=session)
    openai_embedding_service = OpenAIEmbeddingService(
        client=app_config.openAI_client,
        embedding_model=app_config.embedding_model,
        token_store=token_store,
    )
    openai_generation_service = OpenAIGenerationService(
        client=app_config.openAI_client,
        model=app_config.chat_model,
        system_prompt=app_config.system_prompt,
        token_store=token_store,
    )

    rag = RetrievalAugmentedGeneration(
        embedding_service=openai_embedding_service,
        generation_service=openai_generation_service,
        retrieval_service=retrieval_service,
        max_spend=app_config.max_spend,
        token_store=token_store,
        keyword_identification_service=keyword_identifier,
        date=date.today(),
    )

    return await rag.remaining_spend()


@router.get("/health")
async def health(
    session: AsyncSession = Depends(get_database_session),
    app_config: AppConfig = Depends(get_app_config),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> HealthResponse:
    """
    This function is used to check the health of the application. It is used to check if
    the application is running and healthy.

    Returns:
        (JSONResponse): The JSON response with the health status.
    """
    keyword_identifier = get_keyword_identifier(app_config)
    test_vector = EmbeddedChunk(np.random.rand(3072).tolist())  # type: ignore

    token_store = SQLTokenStore(async_session=session)
    openai_embedding_service = OpenAIEmbeddingService(
        client=app_config.openAI_client,
        embedding_model=app_config.embedding_model,
        token_store=token_store,
    )
    openai_generation_service = OpenAIGenerationService(
        client=app_config.openAI_client,
        model=app_config.chat_model,
        system_prompt=app_config.system_prompt,
        token_store=token_store,
    )

    rag = RetrievalAugmentedGeneration(
        embedding_service=openai_embedding_service,
        generation_service=openai_generation_service,
        retrieval_service=retrieval_service,
        max_spend=app_config.max_spend,
        token_store=token_store,
        keyword_identification_service=keyword_identifier,
        date=date.today(),
    )
    test_results = await retrieval_service.retrieve_top_k(test_vector)
    remaining_spend = await rag.remaining_spend()
    spend_left = remaining_spend.remaining_spend
    if test_results is not None and spend_left == 0:
        return HealthResponse("No spend left", spend_left)
    elif test_results is not None and spend_left > 0:
        return HealthResponse("Healthy", spend_left)
    else:
        raise HTTPException(500, "Failed to retrieve top k")


def handle_token_limit_error(
    request: Request, exc: TokenLimitError
) -> StreamingResponse:
    """
    This function is used to handle the token limit error. It is used to catch the token limit
    error and return the appropriate JSON response.

    Args:
        request (Request): The request object.
        exc (TokenLimitError): The token limit error that was raised.

    Returns:
        (JSONResponse): The JSON response with the error message and status code.
    """
    message = "The limit for a question is 8192 tokens. This is a limitation of the OpenAI API. Could you please ask a shorter question?"

    async def event_generator():
        yield message

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def handle_app_errors(request: Request, exc: AppError) -> JSONResponse:
    """
    This function is used to handle the application errors globally. It uses the app error
    pattern discussed in `reference/errors` in the documentation. All the application errors
    are caught and converted to an `AppError`. This method handles the specific instances of
    the `AppError` and returns the appropriate JSON response.

    Args:
        request (Request): The request object.
        exc (AppError): The application error that was raised.

    Returns:
        (JSONResponse): The JSON response with the error message and status code.
    """
    match exc:
        case InputError(message=message):
            return JSONResponse(message, status_code=400)
        case InfraError():
            return JSONResponse(str(exc), status_code=500)
        case MaximumSpendError():
            return JSONResponse(str(exc), status_code=402)
        case _:
            logger.error(f"An unhandled app error occurred: {exc}")
            return JSONResponse(str(exc), status_code=500)


async def exception_callback(request: Request, exc: Exception):
    logger.error(str(exc))
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


def create_app():
    telemetry_enabled = os.getenv("TELEMETRY_ENDPOINT") is not None
    if telemetry_enabled:
        configure_telemetry()
    else:
        logger.warning("Running without telemetry...")

    app = FastAPI(lifespan=lifespan, root_path="/api/v1")
    app.include_router(router)
    app.add_exception_handler(TokenLimitError, handle_token_limit_error)  # type: ignore
    app.add_exception_handler(AppError, handle_app_errors)  # type: ignore
    app.add_exception_handler(Exception, exception_callback)  # type: ignore
    if telemetry_enabled:
        FastAPIInstrumentor.instrument_app(app)

    logger.info("App configured")
    return app


app = create_app()
