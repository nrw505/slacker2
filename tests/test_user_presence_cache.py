import pytest

from datetime import timedelta, datetime
from slacker.user_presence_provider import UserPresenceProvider
from slacker.user_presence_cache import UserPresenceCache


class DummyUPP(UserPresenceProvider):
    users: dict[str, bool]

    def __init__(self) -> None:
        self.users = {}

    def get_user_presence(self, user_id: str) -> bool:
        return self.users.get(user_id, False)

    def set_user_active(self, user_id: str) -> None:
        self.users[user_id] = True

    def set_user_away(self, user_id: str) -> None:
        self.users[user_id] = False


@pytest.fixture
def dummy_user_presence_provider() -> UserPresenceProvider:
    return DummyUPP()


@pytest.fixture
def populated_provider(dummy_user_presence_provider) -> UserPresenceProvider:
    dummy_user_presence_provider.set_user_active("active_user")
    dummy_user_presence_provider.set_user_away("away_user")
    return dummy_user_presence_provider


@pytest.fixture
def cache_provider(populated_provider) -> UserPresenceProvider:
    return UserPresenceCache(provider=populated_provider, expiry=timedelta(minutes=1))


def test_cache_passthrough(cache_provider):
    assert cache_provider.get_user_presence("active_user") is True
    assert cache_provider.get_user_presence("away_user") is False


def test_cache_caches(cache_provider, populated_provider, time_machine):
    # prime the cache
    assert cache_provider.get_user_presence("active_user") is True
    assert cache_provider.get_user_presence("away_user") is False

    # change the backing store
    populated_provider.set_user_away("active_user")
    populated_provider.set_user_active("away_user")

    # verify that we're still returning the cached value
    assert cache_provider.get_user_presence("active_user") is True
    assert cache_provider.get_user_presence("away_user") is False

    time_machine.move_to(datetime.now() + timedelta(minutes=2))

    # verify that the cache expires
    assert cache_provider.get_user_presence("active_user") is False
    assert cache_provider.get_user_presence("away_user") is True
