from abc import ABC, abstractmethod

from slack_sdk.web import WebClient


class UserPresenceProvider(ABC):
    @abstractmethod
    def getUserPresence(self, user_id: str) -> bool:
        ...


class SlackClientUserPresenceProvider(UserPresenceProvider):
    def __init__(self, client: WebClient):
        self.client = client

    def getUserPresence(self, user_id: str) -> bool:
        response = self.client.users_getPresence(user=user_id)
        presence: bool = response.get("presence") == "active"
        return presence


__all__ = ["UserPresenceProvider", "SlackClientUserPresenceProvider"]
