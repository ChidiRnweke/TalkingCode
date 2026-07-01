from talkingcode.services.tools.read_file_tool import ReadFileTool


class FakeDocRepo:
    pass


class FakeRepoRepo:
    pass


def test_read_file_tool_has_schema():
    tool = ReadFileTool(
        document_repository=FakeDocRepo(), repo_repository=FakeRepoRepo()
    )
    assert tool.name is not None
