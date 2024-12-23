from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel


class Language(BaseModel):
    __root__: Optional[Dict[str, int]] = None
