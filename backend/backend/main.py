import logging
from backend.errors import InputError, MaximumSpendError, InfraError
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
    app_config["config"] = AppConfig.from_env(log)
    yield


app = FastAPI(lifespan=lifespan)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with app_config["config"].async_session() as session:
        yield session


def get_openAI_client() -> AsyncOpenAI:
    return app_config["config"].openAI_client


def get_embedding_model() -> str:
    return app_config["config"].embedding_model


def get_top_k() -> int:
    return app_config["config"].top_k


def get_chat_model() -> str:
    return app_config["config"].chat_model


def get_system_prompt() -> str:
    return app_config["config"].system_prompt


def get_openai_embedding_service() -> OpenAIEmbeddingService:
    openAI_client = get_openAI_client()
    embedding_model = get_embedding_model()
    return OpenAIEmbeddingService(client=openAI_client, embedding_model=embedding_model)


def get_openai_generation_service() -> OpenAIGenerationService:
    openAI_client = get_openAI_client()
    chat_model = get_chat_model()
    system_prompt = get_system_prompt()

    return OpenAIGenerationService(
        client=openAI_client,
        chat_model=chat_model,
        system_prompt=system_prompt,
    )


@app.exception_handler(InputError)
async def Input_error_exception_handler(
    request: Request, exc: InputError
) -> JSONResponse:
    log.debug(f"InputError: {exc}")
    return JSONResponse(str(exc), status_code=400)


@app.exception_handler(InfraError)
async def Infra_error_exception_handler(
    request: Request, exc: InfraError
) -> JSONResponse:
    log.error(f"InfraError: {exc}")
    return JSONResponse(str(exc), status_code=500)


@app.exception_handler(MaximumSpendError)
async def max_spend_exception_handler(
    request: Request, exc: MaximumSpendError
) -> JSONResponse:
    log.warning(f"MaximumSpendError: {exc}")
    return JSONResponse(str(exc), status_code=400)


@app.post("/")
async def chat(
    question: InputQuery, session: AsyncSession = Depends(get_session)
) -> RAGResponse:
    rag = RetrievalAugmentedGeneration(
        embedding_service=get_openai_embedding_service(),
        generation_service=get_openai_generation_service(),
        retrieval_service=SQLRetrievalService(session),
    )
    return await rag.retrieval_augmented_generation(question, get_top_k())
