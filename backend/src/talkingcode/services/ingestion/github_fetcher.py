"""GitHub file fetcher service."""

import base64
from dataclasses import dataclass
from typing import Protocol

import httpx
import structlog

from talkingcode.domain.models import GitHubFileContent
from talkingcode.errors import InfraError

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

# File extensions to index
INDEXABLE_EXTENSIONS = {
    ".py",
    ".ts",
    ".js",
    ".svelte",
    ".rs",
    ".go",
    ".java",
    ".rb",
    ".kt",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".sql",
    ".sh",
    ".css",
    ".html",
    ".dockerfile",
    ".tf",
    ".hcl",
}

# File names to index (no extension)
INDEXABLE_NAMES = {"Dockerfile", "Makefile", "Taskfile", "Justfile"}

# Directories to skip
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".svelte-kit",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "target",
    "vendor",
    ".tox",
    "egg-info",
}

MAX_FILE_SIZE_BYTES = 100_000  # 100KB


class IGitHubFetcher(Protocol):
    """Protocol for GitHub file fetching."""

    async def fetch_file_tree(self, owner: str, name: str, ref: str) -> list[str]:
        """Fetch list of indexable file paths in the repo."""

    async def fetch_file_content(
        self, owner: str, name: str, ref: str, path: str
    ) -> GitHubFileContent:
        """Fetch content of a single file."""


@dataclass(slots=True)
class GitHubFetcher:
    """Fetches files from GitHub REST API."""

    github_token: str

    async def fetch_file_tree(self, owner: str, name: str, ref: str) -> list[str]:
        """Fetch list of indexable file paths using the Git Trees API."""
        url = f"https://api.github.com/repos/{owner}/{name}/git/trees/{ref}?recursive=1"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=30.0,
            )

            if response.status_code in (403, 429):
                raise InfraError(f"GitHub rate limit hit: {response.status_code}")
            response.raise_for_status()

            data = response.json()

        paths: list[str] = []
        for item in data.get("tree", []):
            if item.get("type") != "blob":
                continue
            if item.get("size", 0) > MAX_FILE_SIZE_BYTES:
                continue

            path = item["path"]

            parts = path.split("/")
            if any(part in SKIP_DIRS for part in parts):
                continue

            filename = parts[-1]
            if filename in INDEXABLE_NAMES:
                paths.append(path)
                continue

            ext = ""
            if "." in filename:
                ext = "." + filename.rsplit(".", 1)[-1]
            if ext.lower() in INDEXABLE_EXTENSIONS:
                paths.append(path)

        logger.info(
            "Fetched file tree",
            owner=owner,
            name=name,
            ref=ref,
            file_count=len(paths),
        )
        return paths

    async def fetch_file_content(
        self, owner: str, name: str, ref: str, path: str
    ) -> GitHubFileContent:
        """Fetch a single file's content via the Contents API."""
        url = f"https://api.github.com/repos/{owner}/{name}/contents/{path}?ref={ref}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=30.0,
            )

            if response.status_code in (403, 429):
                raise InfraError(
                    f"GitHub rate limit hit for {path}: {response.status_code}"
                )
            response.raise_for_status()

            data = response.json()

        content_b64 = data.get("content", "")
        content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
        sha = data.get("sha", "")

        return GitHubFileContent(path=path, content=content, sha=sha)
