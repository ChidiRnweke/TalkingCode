"""Document classifier using structured output."""
import json
from dataclasses import dataclass
from typing import Protocol

import structlog

from talkingcode.domain.models import DocumentClassificationInput, DocumentClassificationOutput
from talkingcode.enums import Area, FileType
from talkingcode.services.llm.openrouter_client import IOpenRouterClient

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


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
    
    async def classify(
        self,
        input_data: DocumentClassificationInput,
    ) -> DocumentClassificationOutput:
        """Classify a document."""
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
