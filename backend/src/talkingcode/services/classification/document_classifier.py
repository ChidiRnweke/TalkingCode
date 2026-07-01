"""Document classifier using Pydantic AI structured output."""

from dataclasses import dataclass
import re
from typing import Protocol

import structlog
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from talkingcode.domain.models import (
    DocumentClassificationAgentOutput,
    DocumentClassificationInput,
    DocumentClassificationOutput,
)
from talkingcode.enums import Area, FileType
from talkingcode.telemetry.ingestion_metrics import get_ingestion_metrics

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)
metrics = get_ingestion_metrics()


class IDocumentClassifier(Protocol):
    """Protocol for document classifier."""

    async def classify(self, input_data: DocumentClassificationInput) -> DocumentClassificationOutput:
        """Classify a document."""
        ...


@dataclass(slots=True)
class DocumentClassifier:
    """Document classifier using Pydantic AI."""

    openrouter_api_key: str
    model: str = "openai/gpt-4o-mini"
    llm_available: bool = True

    async def classify(
        self,
        input_data: DocumentClassificationInput,
    ) -> DocumentClassificationOutput:
        """Classify a document."""
        if not self.llm_available:
            return self._heuristic_classification(input_data)

        try:
            agent = Agent(
                OpenRouterModel(
                    self.model,
                    provider=OpenRouterProvider(
                        api_key=self.openrouter_api_key,
                        app_url="https://talkingcode.dev",
                        app_title="TalkingCode",
                    ),
                ),
                output_type=DocumentClassificationAgentOutput,
                system_prompt=(
                    "Classify code files. Return language, area, file_type, symbols, and tags. "
                    "Use only valid enum values for area and file_type."
                ),
            )
            result = await agent.run(
                f"File: {input_data.repo}/{input_data.path}\n\n```\n{input_data.content[:4000]}\n```"
            )
            output = result.output
            return DocumentClassificationOutput(
                language=output.language,
                area=output.area,
                file_type=output.file_type,
                symbols=output.symbols,
                tags=output.tags,
            )
        except Exception as exc:  # noqa: BLE001
            metrics.ingestion_classifier_fallback_total.add(
                1, attributes={"operation": "classify", "status": "fallback"}
            )
            logger.warning("Classifier failed; switching to heuristic fallback", error=str(exc))
            self.llm_available = False
            return self._heuristic_classification(input_data)

    def _heuristic_classification(
        self,
        input_data: DocumentClassificationInput,
    ) -> DocumentClassificationOutput:
        """Fallback classifier that avoids LLM dependency."""
        lower = input_data.path.lower()

        if "/tests/" in lower or lower.startswith("tests/") or lower.endswith("_test.py"):
            area = Area.TESTS
            file_type = FileType.TEST
        elif lower.endswith((".md", ".rst", ".txt")):
            area = Area.DOCS
            file_type = FileType.DOCS
        elif any(token in lower for token in ["docker", ".github/", "terraform", ".tf", ".hcl"]):
            area = Area.INFRA
            file_type = FileType.CONFIG
        elif lower.endswith((".svelte", ".tsx", ".jsx", ".css", ".html")):
            area = Area.FRONTEND
            file_type = FileType.SOURCE
        elif lower.endswith((".py", ".go", ".rs", ".java", ".rb", ".ts", ".js")):
            area = Area.BACKEND
            file_type = FileType.SOURCE
        else:
            area = Area.UNKNOWN
            file_type = FileType.UNKNOWN

        ext = input_data.path.rsplit(".", 1)[-1].lower() if "." in input_data.path else ""
        language_map = {
            "py": "python",
            "ts": "typescript",
            "tsx": "typescript",
            "js": "javascript",
            "jsx": "javascript",
            "svelte": "svelte",
            "go": "go",
            "rs": "rust",
            "java": "java",
            "rb": "ruby",
            "md": "markdown",
            "sql": "sql",
            "yaml": "yaml",
            "yml": "yaml",
            "json": "json",
            "toml": "toml",
            "sh": "shell",
            "css": "css",
            "html": "html",
        }
        language = language_map.get(ext, "")

        symbols = re.findall(
            r"\b(?:def|class|function|interface|type)\s+([A-Za-z_][A-Za-z0-9_]*)",
            input_data.content,
        )

        return DocumentClassificationOutput(
            language=language,
            area=area,
            file_type=file_type,
            symbols=symbols[:30],
            tags=[],
        )
