from datetime import date
import logging
import os
from talkingcode.backend.errors import (
    AppError,
    InputError,
    MaximumSpendError,
    InfraError,
)
from fastapi import FastAPI, Depends, Request, APIRouter
from talkingcode.backend.rag import (
    InputQuery,
    RetrievalAugmentedGeneration,
    OpenAIEmbeddingService,
    OpenAIGenerationService,
    SQLRetrievalService,
    RemainingSpend,
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Literal, TypedDict, AsyncIterator
from openai import AsyncOpenAI
from .config import AppConfig, configure_telemetry
from fastapi.responses import StreamingResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from typing import cast

config_key = Literal["config"]
logger = logging.getLogger("app_logger")


router = APIRouter()


class State(TypedDict):
    app_config: AppConfig


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
    yield {"app_config": AppConfig.from_config()}


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
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


def get_openAI_client(request: Request) -> AsyncOpenAI:
    """
    This function is used to get the OpenAI client from the application configuration.
    It returns the OpenAI client from the application configuration.

    Returns:
        (AsyncOpenAI): The OpenAI client.
    """
    config = cast(AppConfig, request.state.app_config)
    return config.openAI_client


def get_embedding_model(request: Request) -> str:
    """
    This function is used to get the embedding model from the application configuration.
    It is required by the `EmbeddingService` to embed the text.

    Returns:
        (str): The name of the text embedding model.
    """
    config = cast(AppConfig, request.state.app_config)
    return config.embedding_model


def get_top_k(request: Request) -> int:
    """
    This function is used to get the top_k value from the application configuration.
    It is used to determine the number of top candidates to return from the model.

    Returns:
        (int): The number of top candidates to return from the model.
    """
    config = cast(AppConfig, request.state.app_config)
    return config.top_k


def get_chat_model(request: Request) -> str:
    """
    This function is used to get the chat model from the application configuration.
    It is required by the `GenerationService` to generate the response.

    Returns:
        (str): The name of the chat model.
    """
    config = cast(AppConfig, request.state.app_config)
    return config.chat_model


def get_system_prompt(request: Request) -> str:
    """
    This function is used to get the system prompt from the application configuration.
    It is required by the `GenerationService` to generate the response.

    Returns:
        (str): The system prompt to use for the chat model.
    """
    config = cast(AppConfig, request.state.app_config)
    return config.system_prompt


def get_max_spend(request: Request) -> float:
    """
    This function is used to get the maximum spend from the application configuration.
    It is used to determine the maximum amount of money that can be spent in a day.

    Returns:
        (float): The maximum amount of money that can be spent in a day.
    """
    config = cast(AppConfig, request.state.app_config)
    return config.max_spend


def get_embedder(request: Request) -> OpenAIEmbeddingService:
    """
    This function is used to get the OpenAI embedding service.
    It is used to embed the text using the OpenAI API. All of the required dependencies
    are transitively provided by the application configuration singleton.

    Returns:
        (OpenAIEmbeddingService): The OpenAI embedding service.
    """
    openAI_client = get_openAI_client(request)
    embedding_model = get_embedding_model(request)
    return OpenAIEmbeddingService(client=openAI_client, embedding_model=embedding_model)


def get_generator(request: Request) -> OpenAIGenerationService:
    """
    This function is used to get the OpenAI generation service.
    It is used to generate the response using the OpenAI API. All of the required dependencies
    are transitively provided by the application configuration singleton.

    Returns:
        (OpenAIGenerationService): The OpenAI generation service.
    """
    openAI_client = get_openAI_client(request)
    chat_model = get_chat_model(request)
    system_prompt = get_system_prompt(request)

    return OpenAIGenerationService(
        client=openAI_client,
        chat_model=chat_model,
        system_prompt=system_prompt,
    )


@router.post("/")
async def chat(
    question: InputQuery,
    session: AsyncSession = Depends(get_session),
    max_spend: float = Depends(get_max_spend),
    top_k: int = Depends(get_top_k),
    openai_embedding_service: OpenAIEmbeddingService = Depends(get_embedder),
    openai_generation_service: OpenAIGenerationService = Depends(get_generator),
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

    Returns:
        (RAGResponse): The response object containing the response and the session ID.
    """

    rag = RetrievalAugmentedGeneration(
        embedding_service=openai_embedding_service,
        generation_service=openai_generation_service,
        retrieval_service=SQLRetrievalService(session),
        max_spend=max_spend,
        date=date.today(),
    )
    id = await rag.validate_and_assign_session_id(question)

    async def event_generator():
        chunk_stream = rag.retrieval_augmented_generation(question, top_k, id)
        async for chunk in chunk_stream:
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Session-ID": id},
    )


@router.get("/remaining_spend")
async def remaining_spend(
    session: AsyncSession = Depends(get_session),
    generation_service: OpenAIGenerationService = Depends(get_generator),
    embedding_service: OpenAIEmbeddingService = Depends(get_embedder),
    max_spend: float = Depends(get_max_spend),
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
    rag = RetrievalAugmentedGeneration(
        embedding_service=embedding_service,
        generation_service=generation_service,
        retrieval_service=SQLRetrievalService(session),
        max_spend=max_spend,
        date=date.today(),
    )
    return await rag.remaining_spend()


def create_app():
    telemetry_enabled = os.getenv("TELEMETRY_ENDPOINT") is not None
    if telemetry_enabled:
        configure_telemetry()
    else:
        logger.warning("Running without telemetry...")

    app = FastAPI(lifespan=lifespan, root_path="/api/v1")
    app.include_router(router)

    if telemetry_enabled:
        FastAPIInstrumentor.instrument_app(app)

    logger.info("App configured")
    return app


app = create_app()


@app.exception_handler(AppError)
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


@app.exception_handler(Exception)
async def exception_callback(request: Request, exc: Exception):
    logger.error(str(exc))
    return JSONResponse(status_code=500, content={"message": "Internal server error"})
