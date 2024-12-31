FROM python:3.12.7-slim-bullseye as base

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache
ENV POETRY_VERSION=1.8.2
ENV POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==$POETRY_VERSION
FROM base as pipelines_base
ENV PRODUCTION=true

COPY ./pipelines /app
COPY shared/ /shared

WORKDIR /app

LABEL org.opencontainers.image.source https://github.com/chidirnweke/talkingcode

RUN poetry check

RUN poetry install --no-interaction --no-cache --without dev