# TalkingCode

The idea behind this project is to create a retrieval augmented generation (RAG) based chatbot that has access to all of your public GitHub code. The project exists of three main components:

1. An ETL pipeline that extracts, transforms and loads the data from the GitHub API to a database. Afterwards, the data is embedded and stored in postgres using the `pgVector` extension.
2. A backend that is capable of taking questions, finding the most relevant code snippets and giving those to chatgpt to generate a response.
3. A frontend that allows you to interact with the chatbot.

The frontend is implemented using Sveltekit. This is a full rebuild of my app,     currently deployed on my VPS and can be accessed [here](https://chat.chidinweke.be). 

The project is dockerized and the relevant images are pushed to my github container registry. 

## Ingestion Security

Repository ingestion is protected by an API key. This allows you to schedule ingestion runs using cron or other automation tools.

1. Set `INGESTION_API_KEY` in your `.env` file (backend).

### Triggering Ingestion

You can trigger ingestion using `curl` with either a header or a query parameter.

**Using Header (Recommended):**
```bash
curl -X POST "https://your-domain.com/api/repos/ingest-owned" \
  -H "X-API-Key: your-secret-key"
```

**Using Query Parameter (Cron-friendly):**
```bash
curl -X POST "https://your-domain.com/api/repos/ingest-owned?api_key=your-secret-key"
```

Note: The `/repos` endpoint remains public for reading repository status, but write actions are restricted.

## Deployment & Observability

### Secrets Management

This project supports loading secrets from **Infisical** or environment variables.

- **Env-only mode (default)**: Just set the variables in `.env`.
- **Infisical mode**: Set `INFISICAL_ENABLED=1` and provide `INFISICAL_CLIENT_ID`, `INFISICAL_CLIENT_SECRET`, `INFISICAL_PROJECT_ID`, `INFISICAL_ENVIRONMENT`, and `INFISICAL_URL`.

### Observability (OpenTelemetry)

Telemetry is supported for traces, metrics, and logs via OTLP.

- Set `OTEL_EXPORTER_OTLP_ENDPOINT` (e.g., `http://localhost:4317`) to enable.
- Ingestion telemetry includes:
  - **Logs**: Detailed per-file and per-run status with timing.
  - **Metrics**: `ingestion_runs_total`, `ingestion_files_total`, `ingestion_file_duration_seconds`, etc.
  - **Traces**: Run-level and stage-level spans.

### Development Stack

Run the full local stack with OTel collector:
```bash
docker compose -f docker-compose.dev.yml up --build
```

### Production Setup

1. **Database Provisioning**:
   The setup profile handles database and role creation idempotently.
   ```bash
   docker compose -f docker-compose.prod.yml --profile setup up backend-migrate
   ```

2. **Deploy App**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```
