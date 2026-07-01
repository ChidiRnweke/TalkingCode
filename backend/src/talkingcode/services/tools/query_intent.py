"""Query intent extraction for auto-detecting metadata filters."""

from dataclasses import dataclass
from typing import Any, Protocol

import structlog
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from talkingcode.domain.models import QueryIntent, QueryIntentAgentOutput

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

INTENT_EXTRACTION_PROMPT = """Extract search metadata from this query.
Available repos: {repo_list}

Query: "{query}"

Rules:
- refined_query: rewrite as one focused natural-language search phrase; do NOT convert into boolean OR keyword lists
- repo_filter: set ONLY if the user explicitly mentions a repo name from the list (use exact format from list)
- language_filter: set ONLY if the query mentions a specific language (use lowercase: python, typescript, etc.)
- area_filter: set ONLY if clear from context. Valid values: backend, frontend, infra, scripts, docs, tests
- file_type_filter: set ONLY if clear. Valid values: source, config, migration, test, docs, ci
- If the question is broad or ambiguous, keep filters null and preserve broad intent in refined_query
- Do not infer narrow assumptions that were not explicitly asked
- When in doubt, leave filters as null — better to search broadly first, then refine in later lookups"""


class IQueryIntentExtractor(Protocol):
    """Protocol for query intent extraction."""

    async def extract_query_intent(
        self,
        query: str,
        openrouter_api_key: str,
        model: str,
        available_repos: list[str],
    ) -> QueryIntent: ...

    def intent_to_filters(self, intent: QueryIntent) -> dict[str, Any]: ...


@dataclass(slots=True)
class QueryIntentExtractor:
    """Extracts metadata filters from natural language queries."""

    async def extract_query_intent(
        self,
        query: str,
        openrouter_api_key: str,
        model: str,
        available_repos: list[str],
    ) -> QueryIntent:
        repo_list = ", ".join(available_repos) if available_repos else "none indexed yet"
        prompt = INTENT_EXTRACTION_PROMPT.format(repo_list=repo_list, query=query)

        try:
            agent = Agent(
                OpenRouterModel(
                    model,
                    provider=OpenRouterProvider(
                        api_key=openrouter_api_key,
                        app_url="https://talkingcode.dev",
                        app_title="TalkingCode",
                    ),
                ),
                output_type=QueryIntentAgentOutput,
            )
            result = await agent.run(prompt)
            output = result.output
            return QueryIntent(
                refined_query=output.refined_query or query,
                repo_filter=output.repo_filter,
                language_filter=output.language_filter,
                area_filter=output.area_filter,
                file_type_filter=output.file_type_filter,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Intent extraction failed, using raw query", query=query, error=str(exc))
            return QueryIntent(refined_query=query)

    def intent_to_filters(self, intent: QueryIntent) -> dict[str, Any]:
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
