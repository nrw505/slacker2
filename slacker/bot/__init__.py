import logging
import re

from threading import Event

from sqlalchemy import create_engine, Engine

from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

from slacker.github import GitHub, PR_RE


class Bot:
    client: SocketModeClient
    db_engine: Engine

    def __init__(
        self, app_token: str, bot_token: str, github_token: str, db_url: str
    ) -> None:
        self.github = GitHub(github_token)
        self.db_engine = create_engine(db_url)
        self.logger = logging.getLogger(__name__)

        client = SocketModeClient(
            app_token=app_token,
            web_client=WebClient(token=bot_token),
        )
        client.logger = self.logger.getChild("client")
        self.client = client

    # Log every event coming from slack
    def log_listener(
        self, client: BaseSocketModeClient, request: SocketModeRequest
    ) -> None:
        print(f"{__name__} - request.type: {request.type}")
        print(f"{__name__} - request.payload: {request.payload}")
        self.logger.info(f"request.type: {request.type}")
        self.logger.info(f"request.payload: {request.payload}")

    def message_listener(
        self, client: BaseSocketModeClient, request: SocketModeRequest
    ) -> None:
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

                if match is None or "!review" not in text:
                    return

                client.web_client.chat_postMessage(
                    channel=event["channel"],
                    text=f"Review request received for {match[0]}",
                )

    def review_listener(
        self, client: BaseSocketModeClient, request: SocketModeRequest
    ) -> None:
        # Is it for me?
        if (
            request.type == "interactive"
            and request.payload.get("type") == "shortcut"
            and request.payload["callback_id"] == "review"
        ):
            # Acknowledge the event
            response = SocketModeResponse(envelope_id=request.envelope_id)
            client.send_socket_mode_response(response)

            # respond to /slacker review
            client.web_client.views_open(
                trigger_id=request.payload["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "review-modal",
                    "title": {"type": "plain_text", "text": "Request a PR review"},
                    "submit": {"type": "plain_text", "text": "Go!"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "pr",
                            "label": {
                                "type": "plain_text",
                                "text": "PR's :github: GitHub URL",
                                "emoji": True,
                            },
                            "element": {
                                "type": "url_text_input",
                                "action_id": "pr_url",
                                "focus_on_load": True,
                            },
                        },
                    ],
                },
            )

        if (
            request.type == "interactive"
            and request.payload.get("type") == "view_submission"
            and request.payload["view"]["callback_id"] == "review-modal"
        ):
            # Check the payload for errors
            response_payload = None
            pr_url = request.payload["view"]["state"]["values"]["pr"]["pr_url"]["value"]

            print(f"PR URL: {pr_url}")
            url_is_good = self.github.valid_pr_url(pr_url)
            if not url_is_good:
                response_payload = {
                    "response_action": "errors",
                    "errors": {
                        "pr": "That is not a GitHub PR URL",
                    },
                }

            # Send the acknowledgement, possibly with errors
            response = SocketModeResponse(
                envelope_id=request.envelope_id, payload=response_payload
            )
            client.send_socket_mode_response(response)

            # If errors, bail out
            if not url_is_good:
                return

            # Assign PR to a reviewer
            # TODO

    def register_listeners(self) -> None:
        self.client.socket_mode_request_listeners.append(self.log_listener)
        self.client.socket_mode_request_listeners.append(self.message_listener)
        self.client.socket_mode_request_listeners.append(self.review_listener)

    def run(self) -> None:
        # Register listeners (we don't do this in __init__ because we
        # need to reference methods that are defined after __init__
        # is)
        self.register_listeners()

        # Start the client (starts a thread)
        self.client.connect()

        # Wait on an event that will never be fulfilled, i.e. loop
        # infinitely and never return.
        Event().wait()
