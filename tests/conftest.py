from typing import Dict
import pytest

from slacker.user_presence_provider import UserPresenceProvider


class DummyUPP(UserPresenceProvider):
    users: Dict[str, bool]

    def __init__(self) -> None:
        self.users = {}

    def getUserPresence(self, user_id: str) -> bool:
        return self.users.get(user_id, False)

    def setUserActive(self, user_id: str) -> None:
        self.users[user_id] = True

    def setUserAway(self, user_id: str) -> None:
        self.users[user_id] = False


@pytest.fixture
def dummy_user_presence_provider() -> UserPresenceProvider:
    return DummyUPP()
