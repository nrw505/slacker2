import os
from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from threading import Event


def process(client: BaseSocketModeClient, req: SocketModeRequest) -> None:
    print(f"request: {req.type}")

    if req.type == "events_api":
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

    if req.type == "interactive" and req.payload.get("type") == "shortcut":
        if req.payload["callback_id"] == "hello-shortcut":
            # Acknowledge
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)

            # Open a modal
            client.web_client.views_open(
                trigger_id=req.payload["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "hello-modal",
                    "title": {"type": "plain_text", "text": "Greetings!"},
                    "submit": {"type": "plain_text", "text": "Good Bye"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": "Hello!"},
                        }
                    ],
                },
            )

    if req.type == "interactive" and req.payload.get("type") == "view_submission":
        if req.payload["view"]["callback_id"] == "hello-modal":
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)


def run(app_token: str, bot_token: str) -> None:
    client = SocketModeClient(
        app_token=app_token,
        web_client=WebClient(token=bot_token),
    )

    client.socket_mode_request_listeners.append(process)
    client.connect()
    Event().wait()


app_token = os.environ.get("SLACK_APP_TOKEN")
bot_token = os.environ.get("SLACK_BOT_TOKEN")

if app_token == None:
    print("SLACK_APP_TOKEN is not set")
if bot_token == None:
    print("SLACK_BOT_TOKEN is not set")

if app_token and bot_token:
    run(app_token, bot_token)
