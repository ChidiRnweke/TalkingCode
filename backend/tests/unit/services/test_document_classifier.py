import pytest

from talkingcode.domain.models import DocumentClassificationInput
from talkingcode.services.classification.document_classifier import DocumentClassifier


@pytest.mark.asyncio
async def test_heuristic_fallback_when_llm_unavailable():
    classifier = DocumentClassifier(
        openrouter_api_key="test-key", llm_available=False
    )
    result = await classifier.classify(
        DocumentClassificationInput(
            repo="test", path="src/main.py", content="def foo(): pass"
        )
    )
    assert result.language is not None
