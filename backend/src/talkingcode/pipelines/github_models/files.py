from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TreeItem(BaseModel):
    path: Optional[str] = Field(None, examples=["test/file.rb"])
    mode: Optional[str] = Field(None, examples=["040000"])
    type: Optional[str] = Field(None, examples=["tree"])
    sha: Optional[str] = Field(
        None, examples=["23f6827669e43831def8a7ad935069c8bd418261"]
    )
    size: Optional[int] = Field(None, examples=[12])
    url: Optional[str] = Field(
        None,
        examples=[
            "https://api.github.com/repos/owner-482f3203ecf01f67e9deb18e/BBB_Private_Repo/git/blobs/23f6827669e43831def8a7ad935069c8bd418261"
        ],
    )


class GitTree(BaseModel):
    sha: str
    url: str
    truncated: bool
    tree: List[TreeItem] = Field(
        ...,
        description="Objects specifying a tree structure",
        examples=[
            {
                "path": "file.rb",
                "mode": "100644",
                "type": "blob",
                "size": 30,
                "sha": "44b4fc6d56897b048c772eb4087f854f46256132",
                "url": "https://api.github.com/repos/octocat/Hello-World/git/blobs/44b4fc6d56897b048c772eb4087f854f46256132",
                "properties": {
                    "path": {"type": "string"},
                    "mode": {"type": "string"},
                    "type": {"type": "string"},
                    "size": {"type": "integer"},
                    "sha": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": ["path", "mode", "type", "sha", "url", "size"],
            }
        ],
    )
