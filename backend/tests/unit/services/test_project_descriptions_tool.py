from talkingcode.services.tools.project_descriptions_tool import (
    ProjectDescriptionsTool,
)


class FakeDocRepo:
    pass


class FakeEmbedder:
    async def embed_batch(self, texts):
        return [[0.1, 0.2]]


def test_tool_has_schema():
    tool = ProjectDescriptionsTool(
        document_repository=FakeDocRepo(),
        embedder=FakeEmbedder(),
    )
    assert tool.name is not None
