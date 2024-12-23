from __future__ import annotations

from typing import Dict, Optional

from pydantic import RootModel


class Languages(RootModel):
    root: Optional[Dict[str, int]] = None
