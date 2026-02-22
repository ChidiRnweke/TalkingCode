from dataclasses import dataclass
from unittest.mock import MagicMock

@dataclass(slots=True)
class ChatController:
    a: int
    b: int

try:
    ChatController(a=1, b=2, config=3)
except TypeError as e:
    print(f"Caught expected error: {e}")
except Exception as e:
    print(f"Caught unexpected error: {e}")
