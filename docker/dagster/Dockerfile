FROM python:3.12.4-slim-bookworm as poetry_base

RUN pip install --no-cache-dir poetry==1.8.3

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM poetry_base as dagster

RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app
ENV PRODUCTION=true

COPY pipelines/dagster.yaml  /opt/dagster/dagster_home/

ENV DAGSTER_HOME=/opt/dagster/dagster_home/

COPY pipelines/ /opt/dagster/app/

COPY shared/ /opt/dagster/shared

WORKDIR /opt/dagster/app

RUN rm dagster.yaml

RUN poetry install --only main --no-root

WORKDIR /opt/dagster/app

EXPOSE 3000

LABEL org.opencontainers.image.source https://github.com/chidirnweke/chatGITpt

ENTRYPOINT ["poetry", "run", "dagster", "dev", "-h", "0.0.0.0", "-p", "3000"]