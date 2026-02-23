"""Document chunker service."""

from dataclasses import dataclass
from typing import Protocol

import structlog

from talkingcode.domain.models import ChunkResult

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


class IChunker(Protocol):
    """Protocol for document chunking."""

    def chunk(self, content: str, max_tokens: int = 512) -> list[ChunkResult]:
        """Split content into chunks."""


@dataclass(slots=True)
class LineChunker:
    """Chunks documents by line groups, respecting a token budget.

    Uses whitespace-split word count as a token approximation.
    Overlap: last 2 lines of previous chunk repeat at start of next.
    """

    overlap_lines: int = 2

    def chunk(self, content: str, max_tokens: int = 512) -> list[ChunkResult]:
        """Split content into chunks."""
        if not content.strip():
            return []

        lines = content.splitlines(keepends=True)
        chunks: list[ChunkResult] = []
        chunk_index = 0
        i = 0

        while i < len(lines):
            current_lines: list[str] = []
            current_tokens = 0
            start_line = i + 1

            while i < len(lines):
                line_tokens = len(lines[i].split())
                if current_tokens + line_tokens > max_tokens and current_lines:
                    break
                current_lines.append(lines[i])
                current_tokens += line_tokens
                i += 1

            if not current_lines:
                break

            end_line = start_line + len(current_lines) - 1
            chunk_content = "".join(current_lines)

            chunks.append(
                ChunkResult(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    token_count=current_tokens,
                    start_line=start_line,
                    end_line=end_line,
                )
            )

            chunk_index += 1

            if i < len(lines) and self.overlap_lines > 0:
                i = max(
                    i - self.overlap_lines,
                    start_line + len(current_lines) - self.overlap_lines,
                )

        logger.debug("Chunked document", chunk_count=len(chunks), total_lines=len(lines))
        return chunks
