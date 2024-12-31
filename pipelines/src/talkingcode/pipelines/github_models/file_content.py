from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class FieldLinks(BaseModel):
    git: Optional[str]
    html: Optional[str]
    self: str


class Entry(BaseModel):
    type: str
    size: int
    name: str
    path: str
    sha: str
    url: str
    git_url: Optional[str]
    html_url: Optional[str]
    download_url: Optional[str]
    field_links: FieldLinks = Field(..., alias="_links")


class ContentTree(BaseModel):
    type: str
    size: int
    name: str
    path: str
    sha: str
    content: Optional[str] = None
    url: str
    git_url: Optional[str]
    html_url: Optional[str]
    download_url: Optional[str]
    entries: Optional[List[Entry]] = None
    field_links: FieldLinks = Field(..., alias="_links")
