import os
import logging
from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from threading import Event

from .review_listener import review_listener
from .logging_listener import logging_listener
from .acknowledge_listener import acknowledge_listener


def run(app_token: str, bot_token: str) -> None:
    client = SocketModeClient(
        app_token=app_token,
        web_client=WebClient(token=bot_token),
    )

    client.logger = logging.getLogger(__name__)
    client.socket_mode_request_listeners.append(review_listener)
    client.socket_mode_request_listeners.append(logging_listener)
    client.socket_mode_request_listeners.append(acknowledge_listener)
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
