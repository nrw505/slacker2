import re

from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.listeners import SocketModeRequestListener

PR_RE = re.compile("https://github.com/([^/]*)/([^/]*)/pull/([0-9]*)")


def message_listener(client: BaseSocketModeClient, request: SocketModeRequest) -> None:
    # Is it a message in a channel?
    if request.type == "events_api":
        event = request.payload.get("event")
        if event is None:
            print("No event")
            return

        if event["type"] == "message":
            # Acknowledge the event
            response = SocketModeResponse(envelope_id=request.envelope_id)
            client.send_socket_mode_response(response)

            text = event["text"]
            match = PR_RE.search(text)

            print(f"text = f{text}")
            print(f"match = f{match}")
            if match is None or "!review" not in text:
                return

            client.web_client.chat_postMessage(
                channel=event["channel"],
                text=f"Review request received for {match[0]}",
            )
