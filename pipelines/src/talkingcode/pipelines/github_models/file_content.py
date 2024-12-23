from __future__ import annotations

from typing import List, Optional

from pydantic import AnyUrl, BaseModel, Field


class FieldLinks(BaseModel):
    git: Optional[AnyUrl]
    html: Optional[AnyUrl]
    self: AnyUrl


class Entry(BaseModel):
    type: str
    size: int
    name: str
    path: str
    sha: str
    url: AnyUrl
    git_url: Optional[AnyUrl]
    html_url: Optional[AnyUrl]
    download_url: Optional[AnyUrl]
    field_links: FieldLinks = Field(..., alias="_links")


class ContentTree(BaseModel):
    type: str
    size: int
    name: str
    path: str
    sha: str
    content: Optional[str] = None
    url: AnyUrl
    git_url: Optional[AnyUrl]
    html_url: Optional[AnyUrl]
    download_url: Optional[AnyUrl]
    entries: Optional[List[Entry]] = None
    field_links: FieldLinks = Field(..., alias="_links")
