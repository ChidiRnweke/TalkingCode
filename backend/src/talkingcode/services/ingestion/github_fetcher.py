"""GitHub file fetcher service."""

import base64
import time
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import parse_qs, urlparse

import httpx
import structlog
from talkingcode.domain.models import GitHubFileContent, GitHubRepository
from talkingcode.errors import InfraError
from talkingcode.telemetry.ingestion_metrics import get_ingestion_metrics

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)
metrics = get_ingestion_metrics()

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

# Low-signal files to skip even when extension is indexable
SKIP_FILENAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
}

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

    async def list_owned_repositories(self) -> list[GitHubRepository]:
        """List repositories owned by the authenticated GitHub user."""
        ...

    async def fetch_file_tree(self, owner: str, name: str, ref: str) -> list[str]:
        """Fetch list of indexable file paths in the repo."""
        ...

    async def fetch_file_content(
        self, owner: str, name: str, ref: str, path: str
    ) -> GitHubFileContent:
        """Fetch content of a single file."""
        ...


@dataclass(slots=True)
class GitHubFetcher:
    """Fetches files from GitHub REST API."""

    github_token: str

    async def list_owned_repositories(self) -> list[GitHubRepository]:
        """List non-fork repositories owned by the authenticated user."""
        repos: list[GitHubRepository] = []
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                t0 = time.perf_counter()
                response = await client.get(
                    "https://api.github.com/user/repos",
                    headers={
                        "Authorization": f"token {self.github_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    params={
                        "type": "owner",
                        "sort": "updated",
                        "per_page": 100,
                        "page": page,
                    },
                    timeout=30.0,
                )

                elapsed = time.perf_counter() - t0
                status_class = f"{response.status_code // 100}xx"
                metrics.ingestion_github_requests_total.add(
                    1,
                    attributes={
                        "operation": "list_owned_repositories",
                        "status_class": status_class,
                        "provider": "github",
                    },
                )
                metrics.ingestion_github_request_duration_seconds.record(
                    elapsed,
                    attributes={
                        "operation": "list_owned_repositories",
                        "status_class": status_class,
                        "provider": "github",
                    },
                )

                if response.status_code in (403, 429):
                    raise InfraError(f"GitHub rate limit hit: {response.status_code}")
                response.raise_for_status()

                payload = response.json()
                if not payload:
                    break

                for item in payload:
                    owner = item.get("owner", {}).get("login")
                    name = item.get("name")
                    default_branch = item.get("default_branch")
                    is_fork = bool(item.get("fork", False))

                    if not owner or not name or not default_branch or is_fork:
                        continue

                    repos.append(
                        GitHubRepository(
                            owner=owner,
                            name=name,
                            default_branch=default_branch,
                            is_fork=is_fork,
                        )
                    )

                if not self._has_next_page(response.headers.get("Link", "")):
                    break
                page += 1

        logger.info("Fetched owned repositories", repo_count=len(repos))
        return repos

    async def fetch_file_tree(self, owner: str, name: str, ref: str) -> list[str]:
        """Fetch list of indexable file paths using the Git Trees API."""
        url = f"https://api.github.com/repos/{owner}/{name}/git/trees/{ref}?recursive=1"

        t0 = time.perf_counter()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=30.0,
            )

            elapsed = time.perf_counter() - t0
            status_class = f"{response.status_code // 100}xx"
            metrics.ingestion_github_requests_total.add(
                1,
                attributes={
                    "operation": "fetch_file_tree",
                    "status_class": status_class,
                    "provider": "github",
                },
            )
            metrics.ingestion_github_request_duration_seconds.record(
                elapsed,
                attributes={
                    "operation": "fetch_file_tree",
                    "status_class": status_class,
                    "provider": "github",
                },
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
            if filename in SKIP_FILENAMES:
                continue

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

        t0 = time.perf_counter()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=30.0,
            )

            elapsed = time.perf_counter() - t0
            status_class = f"{response.status_code // 100}xx"
            metrics.ingestion_github_requests_total.add(
                1,
                attributes={
                    "operation": "fetch_file_content",
                    "status_class": status_class,
                    "provider": "github",
                },
            )
            metrics.ingestion_github_request_duration_seconds.record(
                elapsed,
                attributes={
                    "operation": "fetch_file_content",
                    "status_class": status_class,
                    "provider": "github",
                },
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

    @staticmethod
    def _has_next_page(link_header: str) -> bool:
        """Check if a GitHub Link header includes a next page."""
        if not link_header:
            return False

        for part in link_header.split(","):
            if 'rel="next"' not in part:
                continue

            url = part.split(";", 1)[0].strip().strip("<>")
            parsed = urlparse(url)
            page = parse_qs(parsed.query).get("page")
            return bool(page)

        return False
