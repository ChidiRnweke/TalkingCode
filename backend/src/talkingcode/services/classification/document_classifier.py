"""Document classifier using structured output."""
import json
from dataclasses import dataclass
import re
from typing import Protocol

import structlog

from talkingcode.domain.models import DocumentClassificationInput, DocumentClassificationOutput
from talkingcode.enums import Area, FileType
from talkingcode.services.llm.openrouter_client import IOpenRouterClient
from talkingcode.telemetry.ingestion_metrics import get_ingestion_metrics

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)
metrics = get_ingestion_metrics()


class IDocumentClassifier(Protocol):
    """Protocol for document classifier."""
    
    async def classify(self, input_data: DocumentClassificationInput) -> DocumentClassificationOutput:
        """Classify a document."""
        ...

CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string", "description": "Programming language"},
        "area": {"type": "string", "enum": [a.value for a in Area]},
        "file_type": {"type": "string", "enum": [ft.value for ft in FileType]},
        "symbols": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["language", "area", "file_type", "symbols", "tags"],
}


@dataclass(slots=True)
class DocumentClassifier:
    """Document classifier using OpenRouter."""

    openrouter_client: IOpenRouterClient
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
            content = await self.openrouter_client.send_chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Classify this code file. Return JSON with language, area (backend/frontend/infra/scripts/docs/tests), file_type (source/config/migration/test/docs/ci/unknown), symbols (function/class names), and tags.",
                    },
                    {
                        "role": "user",
                        "content": f"File: {input_data.repo}/{input_data.path}\n\n```\n{input_data.content[:4000]}\n```",
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "document_classification",
                        "strict": True,
                        "schema": CLASSIFICATION_SCHEMA,
                    },
                },
            )

            parsed = json.loads(content)

            return DocumentClassificationOutput(
                language=parsed.get("language", ""),
                area=Area(parsed.get("area", Area.UNKNOWN.value)),
                file_type=FileType(parsed.get("file_type", FileType.UNKNOWN.value)),
                symbols=parsed.get("symbols", []),
                tags=parsed.get("tags", []),
            )
        except Exception as exc:  # noqa: BLE001
            metrics.ingestion_classifier_fallback_total.add(1, attributes={"operation": "classify", "status": "fallback"})
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
