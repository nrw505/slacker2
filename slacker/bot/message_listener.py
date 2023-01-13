from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.listeners import SocketModeRequestListener


def message_listener(client: BaseSocketModeClient, request: SocketModeRequest) -> None:
    # Is it a message in a channel?
    if request.type == "events_api":
        if request.payload.get("event")["type"] == "message":
            event = request.payload.get("event")
