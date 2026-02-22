"""Query intent extraction for auto-detecting metadata filters."""
import json
from dataclasses import dataclass
from typing import Any

import structlog

from talkingcode.services.llm.openrouter_client import IOpenRouterClient

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

INTENT_EXTRACTION_PROMPT = """Extract search metadata from this query. Return JSON only.
Available repos: {repo_list}

Query: "{query}"

Schema: {{ "refined_query": string, "repo_filter": string|null, "language_filter": string|null, "area_filter": string|null, "file_type_filter": string|null }}

Rules:
- refined_query: rewrite the query as a concise search phrase (remove filler words)
- repo_filter: set ONLY if the user explicitly mentions a repo name from the list (use exact format from list)
- language_filter: set ONLY if the query mentions a specific language (use lowercase: python, typescript, etc.)
- area_filter: set ONLY if clear from context. Valid values: backend, frontend, infra, scripts, docs, tests
- file_type_filter: set ONLY if clear. Valid values: source, config, migration, test, docs, ci
- When in doubt, leave filters as null — better to search broadly than miss results"""


@dataclass(frozen=True)
class QueryIntent:
    """Extracted metadata hints from a natural language query."""

    refined_query: str
    repo_filter: str | None = None
    language_filter: str | None = None
    area_filter: str | None = None
    file_type_filter: str | None = None


async def extract_query_intent(
    query: str,
    openrouter_client: IOpenRouterClient,
    model: str,
    available_repos: list[str],
) -> QueryIntent:
    """Extract metadata filters from a natural language query using a cheap LLM."""
    repo_list = ", ".join(available_repos) if available_repos else "none indexed yet"
    prompt = INTENT_EXTRACTION_PROMPT.format(repo_list=repo_list, query=query)

    try:
        response = await openrouter_client.send_chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        data = json.loads(response)
        return QueryIntent(
            refined_query=data.get("refined_query", query),
            repo_filter=data.get("repo_filter"),
            language_filter=data.get("language_filter"),
            area_filter=data.get("area_filter"),
            file_type_filter=data.get("file_type_filter"),
        )
    except Exception:
        logger.warning("Intent extraction failed, using raw query", query=query)
        return QueryIntent(refined_query=query)


def intent_to_filters(intent: QueryIntent) -> dict[str, Any]:
    """Convert QueryIntent to a filters dict for DocumentRepository.search_chunks."""
    filters: dict[str, Any] = {}
    if intent.repo_filter:
        filters["repository_name"] = intent.repo_filter
    if intent.language_filter:
        filters["language"] = intent.language_filter
    if intent.area_filter:
        filters["area"] = intent.area_filter
    if intent.file_type_filter:
        filters["file_type"] = intent.file_type_filter
    return filters
