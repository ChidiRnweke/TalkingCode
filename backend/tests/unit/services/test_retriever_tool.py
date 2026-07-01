from talkingcode.services.tools.retriever_tool import RetrieverTool


class FakeDocRepo:
    pass


class FakeEmbedder:
    async def embed_batch(self, texts):
        return [[0.1, 0.2]]


class FakeIntentExtractor:
    pass


def test_retriever_tool_has_schema():
    tool = RetrieverTool(
        document_repository=FakeDocRepo(),
        embedder=FakeEmbedder(),
        intent_extractor=FakeIntentExtractor(),
        openrouter_api_key="test-key",
    )
    assert tool.schema is not None
