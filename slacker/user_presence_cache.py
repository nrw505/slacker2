from typing import Optional

from datetime import datetime, timedelta
from dataclasses import dataclass

from slack_sdk.web import WebClient

from slacker.user_presence_provider import UserPresenceProvider

DEFAULT_CACHE_EXPIRY = timedelta(minutes=10)


@dataclass
class UserPresenceCacheEntry:
    user_id: str
    presence: bool
    fetched: datetime


class UserPresenceCache(UserPresenceProvider):
    provider: UserPresenceProvider
    cache: dict[str, UserPresenceCacheEntry]
    expiry: timedelta

    def __init__(
        self,
        provider: UserPresenceProvider,
        expiry: timedelta = DEFAULT_CACHE_EXPIRY,
    ):
        self.provider = provider
        self.cache = {}
        self.expiry = expiry

    def getUserPresence(self, user_id: str) -> bool:
        entry = self.cache.get(user_id)
        now = datetime.now()

        if entry is None or (now - entry.fetched) > self.expiry:
            presence = self.provider.getUserPresence(user_id)
            entry = UserPresenceCacheEntry(
                user_id=user_id,
                presence=presence,
                fetched=now,
            )
            self.cache[user_id] = entry

        return entry.presence


__all__ = ["UserPresenceCache"]
