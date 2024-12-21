from datetime import date
import logging
import os
from backend.telemetry import configure_telemetry
from backend.errors import AppError, InputError, MaximumSpendError, InfraError
from fastapi import FastAPI, Depends, Request, APIRouter
from backend.rag import (
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
from typing import AsyncGenerator, Literal
from openai import AsyncOpenAI
from .config import AppConfig
from fastapi.responses import StreamingResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

config_key = Literal["config"]
logger = logging.getLogger("backend_logger")


app_config: dict[config_key, AppConfig] = {}


router = APIRouter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function is used to manage the lifespan of the FastAPI application.
    It is used to set up the application configuration and store it as a singleton.
    This singleton is then used to provide configuration to the application's dependencies.
    The configuration contains the database session, OpenAI client, and other configuration values.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    app_config["config"] = AppConfig.from_config()
    yield


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    This function is used to get an async session from the application configuration.
    It draws the session from the application configuration and yields it to the caller.
    This way we are certain that a new session is created for each request.

    Returns:
        AsyncGenerator[AsyncSession, None]: The async session generator.

    Yields:
        (Iterator[AsyncGenerator[AsyncSession, None]]): The async session generator.
    """
    async with app_config["config"].async_session() as session:
        yield session


def get_openAI_client() -> AsyncOpenAI:
    """
    This function is used to get the OpenAI client from the application configuration.
    It returns the OpenAI client from the application configuration.

    Returns:
        (AsyncOpenAI): The OpenAI client.
    """
    return app_config["config"].openAI_client


def get_embedding_model() -> str:
    """
    This function is used to get the embedding model from the application configuration.
    It is required by the `EmbeddingService` to embed the text.

    Returns:
        (str): The name of the text embedding model.
    """
    return app_config["config"].embedding_model


def get_top_k() -> int:
    """
    This function is used to get the top_k value from the application configuration.
    It is used to determine the number of top candidates to return from the model.

    Returns:
        (int): The number of top candidates to return from the model.
    """
    return app_config["config"].top_k


def get_chat_model() -> str:
    """
    This function is used to get the chat model from the application configuration.
    It is required by the `GenerationService` to generate the response.

    Returns:
        (str): The name of the chat model.
    """
    return app_config["config"].chat_model


def get_system_prompt() -> str:
    """
    This function is used to get the system prompt from the application configuration.
    It is required by the `GenerationService` to generate the response.

    Returns:
        (str): The system prompt to use for the chat model.
    """
    return app_config["config"].system_prompt


def get_max_spend() -> float:
    """
    This function is used to get the maximum spend from the application configuration.
    It is used to determine the maximum amount of money that can be spent in a day.

    Returns:
        (float): The maximum amount of money that can be spent in a day.
    """
    return app_config["config"].max_spend


def get_openai_embedding_service() -> OpenAIEmbeddingService:
    """
    This function is used to get the OpenAI embedding service.
    It is used to embed the text using the OpenAI API. All of the required dependencies
    are transitively provided by the application configuration singleton.

    Returns:
        (OpenAIEmbeddingService): The OpenAI embedding service.
    """
    openAI_client = get_openAI_client()
    embedding_model = get_embedding_model()
    return OpenAIEmbeddingService(client=openAI_client, embedding_model=embedding_model)


def get_openai_generation_service() -> OpenAIGenerationService:
    """
    This function is used to get the OpenAI generation service.
    It is used to generate the response using the OpenAI API. All of the required dependencies
    are transitively provided by the application configuration singleton.

    Returns:
        (OpenAIGenerationService): The OpenAI generation service.
    """
    openAI_client = get_openAI_client()
    chat_model = get_chat_model()
    system_prompt = get_system_prompt()

    return OpenAIGenerationService(
        client=openAI_client,
        chat_model=chat_model,
        system_prompt=system_prompt,
    )


@router.post("/")
async def chat(question: InputQuery, session: AsyncSession = Depends(get_session)):
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
    max_spend = get_max_spend()
    rag = RetrievalAugmentedGeneration(
        embedding_service=get_openai_embedding_service(),
        generation_service=get_openai_generation_service(),
        retrieval_service=SQLRetrievalService(session),
        max_spend=max_spend,
        date=date.today(),
    )
    id = await rag.validate_and_assign_session_id(question)

    async def event_generator():
        chunk_stream = rag.retrieval_augmented_generation(question, get_top_k(), id)
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
    max_spend = get_max_spend()
    rag = RetrievalAugmentedGeneration(
        embedding_service=get_openai_embedding_service(),
        generation_service=get_openai_generation_service(),
        retrieval_service=SQLRetrievalService(session),
        max_spend=max_spend,
        date=date.today(),
    )
    return await rag.remaining_spend()


def create_app():
    no_telemetry = os.getenv("TELEMETRY_DISABLED")
    if no_telemetry:
        logger.warning("Running app in development mode without telemetry...")
    else:
        configure_telemetry()

    app = FastAPI(lifespan=lifespan, root_path="/api/v1")
    app.include_router(router)

    if not no_telemetry:
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
