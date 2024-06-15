FROM python:3.12.4-slim-bookworm as poetry_base

RUN pip install --no-cache-dir poetry==1.8.3

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM poetry_base as dagster

RUN mkdir -p /app
WORKDIR /app
COPY dataprocessing/ /app
COPY shared/ /shared
RUN poetry install --only main --no-root

ENV DAGSTER_HOME=/app

COPY . /app

WORKDIR /app

ENTRYPOINT ["poetry", "run", "dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]