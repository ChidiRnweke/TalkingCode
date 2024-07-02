from datetime import date
import logging
from backend.errors import AppError, InputError, MaximumSpendError, InfraError
from backend.retrieval_augmented_generation.retrieve import RemainingSpend
from fastapi import FastAPI, Depends, Request
from backend.retrieval_augmented_generation import (
    InputQuery,
    RAGResponse,
    RetrievalAugmentedGeneration,
    OpenAIEmbeddingService,
    OpenAIGenerationService,
    SQLRetrievalService,
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Literal
from openai import AsyncOpenAI
from .config import AppConfig

config_key = Literal["config"]
log = logging.getLogger("backend_logger")


app_config: dict[config_key, AppConfig] = {}


app = FastAPI(root_path="/api/v1")


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
    app_config["config"] = AppConfig.from_env(log)
    yield


app = FastAPI(lifespan=lifespan)


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
            log.error(f"An unhandled app error occurred: {exc}")
            return JSONResponse(str(exc), status_code=500)


@app.post("/")
async def chat(
    question: InputQuery, session: AsyncSession = Depends(get_session)
) -> RAGResponse:
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
    return await rag.retrieval_augmented_generation(question, get_top_k())


@app.get("/remaining_spend")
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
