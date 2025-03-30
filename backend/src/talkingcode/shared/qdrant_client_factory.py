from typing import Dict, Optional

import structlog
from qdrant_client import AsyncQdrantClient

logger: structlog.stdlib.BoundLogger = structlog.getLogger("talkingcode")

# Global singleton instance for local client
_local_client_instances: Dict[str, AsyncQdrantClient] = {}


def get_qdrant_client(
    server_mode: bool,
    server_url: Optional[str] = None,
    api_key: Optional[str] = None,
    local_storage_path: str = "../qdrant-data",
) -> AsyncQdrantClient:
    """
    Factory function to get a Qdrant client.

    In server mode, it always returns a new client instance.
    In local mode, it returns a cached client to avoid the "Storage folder is already accessed" error.

    Args:
        server_mode: Whether to connect to a Qdrant server or use local storage
        server_url: URL of the Qdrant server (required if server_mode is True)
        api_key: API key for the Qdrant server (required if server_mode is True)
        local_storage_path: Path to the local storage folder (used if server_mode is False)

    Returns:
        AsyncQdrantClient: Qdrant client instance
    """
    if server_mode:
        if not server_url:
            raise ValueError("server_url is required when server_mode is True")

        logger.debug("Creating new Qdrant server client instance", url=server_url)
        return AsyncQdrantClient(url=server_url, api_key=api_key)
    else:
        # For local mode, use the cached client if it exists
        if local_storage_path not in _local_client_instances:
            logger.debug(
                "Creating new Qdrant local client instance", path=local_storage_path
            )
            _local_client_instances[local_storage_path] = AsyncQdrantClient(
                path=local_storage_path
            )
        else:
            logger.debug(
                "Reusing existing Qdrant local client instance", path=local_storage_path
            )

        return _local_client_instances[local_storage_path]
