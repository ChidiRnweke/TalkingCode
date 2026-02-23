# TalkingCode

The idea behind this project is to create a retrieval augmented generation (RAG) based chatbot that has access to all of your public GitHub code. The project exists of three main components:

1. An ETL pipeline that extracts, transforms and loads the data from the GitHub API to a database. Afterwards, the data is embedded and stored in postgres using the `pgVector` extension.
2. A backend that is capable of taking questions, finding the most relevant code snippets and giving those to chatgpt to generate a response.
3. A frontend that allows you to interact with the chatbot.

The frontend is implemented using Sveltekit. This is a full rebuild of my app, currently deployed on my VPS and can be accessed [here](https://chat.chidinweke.be). 

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
