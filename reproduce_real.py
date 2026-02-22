from unittest.mock import MagicMock
from talkingcode.factory import AppFactory
from talkingcode.config import AppConfig

# Mock config
config = MagicMock(spec=AppConfig)
session = MagicMock()

factory = AppFactory(session=session, config=config)
try:
    controller = factory.get_chat_controller()
    print("Success")
except Exception as e:
    print(f"Failed: {e}")
