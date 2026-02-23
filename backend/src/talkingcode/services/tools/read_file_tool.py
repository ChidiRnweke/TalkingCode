"""Tool for reading file contents from the vector store."""
from dataclasses import dataclass
from typing import Any

import structlog

from talkingcode.repository.document_repository import DocumentRepository
from talkingcode.repository.repo_repository import RepoRepository

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@dataclass(slots=True)
class ReadFileTool:
    """Tool that reads file content reconstructed from stored chunks."""

    document_repository: DocumentRepository
    repo_repository: RepoRepository

    name: str = "read_file"
    timeout: int = 10

    @property
    def schema(self) -> dict[str, Any]:
        """Tool schema."""
        return {
            "description": (
                "Read the contents of a specific file from an indexed repository. "
                "Returns the file content reconstructed from stored chunks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in 'owner/name' format",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file within the repository",
                    },
                },
                "required": ["repository", "file_path"],
                "additionalProperties": False,
            },
        }

    async def execute(self, repository: str, file_path: str) -> dict[str, Any]:
        """Read a file's stored chunks and return reassembled content."""
        if "/" not in repository:
            return {"error": f"Invalid repository format: {repository}. Use 'owner/name'."}

        owner, name = repository.split("/", 1)
        repo = await self.repo_repository.get_by_owner_name(owner, name)

        if not repo:
            return {"error": f"Repository {repository} is not indexed."}

        chunks = await self.document_repository.get_file_chunks(repo.id, file_path)

        if chunks is None:
            return {"error": f"File {file_path} not found in {repository}."}

        content_parts = [c["content"] for c in chunks]
        full_content = "\n".join(content_parts)

        metadata = chunks[0] if chunks else {}

        return {
            "repository": repository,
            "file_path": file_path,
            "language": metadata.get("language", ""),
            "area": metadata.get("area", ""),
            "file_type": metadata.get("file_type", ""),
            "symbols": metadata.get("symbols", []),
            "chunk_count": len(chunks),
            "content": full_content,
        }
