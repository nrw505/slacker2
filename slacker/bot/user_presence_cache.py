from typing import Dict

from datetime import datetime, timedelta
from dataclasses import dataclass

from slack_sdk.web import WebClient

CACHE_EXPIRY = timedelta(minutes=10)


@dataclass
class UserPresenceCacheEntry:
    user_id: str
    presence: bool
    fetched: datetime


class UserPresenceCache:
    client: WebClient
    cache: Dict[str, UserPresenceCacheEntry]

    def __init__(self, client: WebClient):
        self.client = client
        self.cache = {}

    def getUserPresence(self, user_id: str) -> bool:
        entry = self.cache.get(user_id)
        now = datetime.now()

        if entry is None or (now - entry.fetched) > CACHE_EXPIRY:
            response = self.client.users_getPresence(user=user_id)
            entry = UserPresenceCacheEntry(
                user_id=user_id,
                presence=(response.get("presence") == "active"),
                fetched=now,
            )
            self.cache[user_id] = entry

        return entry.presence


__all__ = ["UserPresenceCache"]
