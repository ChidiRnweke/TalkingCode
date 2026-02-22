"""Document classifier using structured output."""
import json
from dataclasses import dataclass

import httpx
import structlog

from talkingcode.domain.models import DocumentClassificationOutput
from talkingcode.domain.services import DocumentClassificationInput
from talkingcode.enums import Area, FileType

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

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
    """Document classifier using OpenAI."""
    
    openai_api_key: str
    
    async def classify(
        self,
        input_data: DocumentClassificationInput,
    ) -> DocumentClassificationOutput:
        """Classify a document."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Classify this code file. Return JSON with language, area (backend/frontend/infra/scripts/docs/tests), file_type (source/config/migration/test/docs/ci/unknown), symbols (function/class names), and tags.",
                        },
                        {
                            "role": "user",
                            "content": f"File: {input_data.repo}/{input_data.path}\n\n```\n{input_data.content[:4000]}\n```",
                        },
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "document_classification",
                            "strict": True,
                            "schema": CLASSIFICATION_SCHEMA,
                        },
                    },
                },
                timeout=30.0,
            )
            
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            return DocumentClassificationOutput(
                language=parsed.get("language", ""),
                area=Area(parsed.get("area", Area.UNKNOWN.value)),
                file_type=FileType(parsed.get("file_type", FileType.UNKNOWN.value)),
                symbols=parsed.get("symbols", []),
                tags=parsed.get("tags", []),
            )
