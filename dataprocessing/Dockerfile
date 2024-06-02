FROM python:3.12-slim as poetry_base

COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry==1.8.3
RUN poetry export -f requirements.txt --without-hashes > requirements.txt

FROM python:3.12-slim as base

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl gnupg2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=poetry_base /requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

FROM base as dagster

ENV DAGSTER_HOME=/app

RUN mkdir -p /app

COPY . /app

WORKDIR /app

EXPOSE 3000

ENTRYPOINT ["dagster", "dev", "-h", "0.0.0.0", "-p", "3000"]