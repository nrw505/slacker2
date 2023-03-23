import logging
import re
import random
from datetime import datetime

from threading import Event

from sqlalchemy import create_engine, Engine
from sqlalchemy import select
from sqlalchemy.orm import Session

from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

from slacker.github import GitHub, PR_RE

from slacker.data_broker import DataBroker
from slacker.actions.assign_review import AssignReview

from slacker.model import User, Channel, UserChannelConfig, AssignedReview


class Bot:
    client: SocketModeClient
    db_engine: Engine
    broker: DataBroker

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
        self.broker = DataBroker(client.web_client)

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
                self.logger.error("No event in events_api message?!")
                return

            if event["type"] == "message":
                # Acknowledge the event
                response = SocketModeResponse(envelope_id=request.envelope_id)
                client.send_socket_mode_response(response)

                text = event["text"]
                match = PR_RE.search(text)

                if match is None or "!review" not in text:
                    return

                self.assign_review(event["user"], event["channel"], match[0])

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
                        {
                            "type": "input",
                            "block_id": "channel",
                            "label": {
                                "type": "plain_text",
                                "text": "Channel",
                                "emoji": True,
                            },
                            "element": {
                                "type": "channels_select",
                                "action_id": "channel",
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
            channel = request.payload["view"]["state"]["values"]["channel"]["channel"][
                "selected_channel"
            ]

            errors: dict[str, str] = {}

            url_is_good = self.github.valid_pr_url(pr_url)
            if not url_is_good:
                errors["pr"] = "That is not a GitHub PR URL"

            if not channel:
                errors["channel"] = "Must select a channel"

            if any(errors):
                response_payload = {
                    "response_action": "errors",
                    "errors": errors,
                }

            # Send the acknowledgement, possibly with errors
            response = SocketModeResponse(
                envelope_id=request.envelope_id, payload=response_payload
            )
            client.send_socket_mode_response(response)

            # If errors, bail out
            if any(errors):
                return

            # Assign PR to a reviewer
            self.assign_review(request.payload["user"]["id"], channel, pr_url)

    def register_listeners(self) -> None:
        self.client.socket_mode_request_listeners.append(self.log_listener)
        self.client.socket_mode_request_listeners.append(self.message_listener)
        self.client.socket_mode_request_listeners.append(self.review_listener)

    def send_text_to_channel(self, channel: str, text: str) -> None:
        self.client.web_client.chat_postMessage(channel=channel, text=text)

    def assign_review(self, requestor: str, channel: str, pr_url: str) -> None:
        self.logger.warning(
            f"assigning review for {pr_url} (requested by {requestor} in {channel})"
        )
        self.send_text_to_channel(channel, f"Review request received for {pr_url}")

        pr = self.github.pr(pr_url)

        with Session(self.db_engine) as session:
            action = AssignReview(self.broker)
            result = action.perform(session, requestor, channel, pr)

            if not result.successful:
                for error in result.errors:
                    self.send_text_to_channel(channel, error)
                return

            for message in result.messages:
                self.send_text_to_channel(channel, message)

            reviewer = result.reviewer
            if reviewer is None:
                self.send_text_to_channel(
                    channel,
                    "No reviewer assigned but AssignReview action was successful!?",
                )
            else:
                self.send_text_to_channel(
                    channel,
                    f"{reviewer.name} (<@{reviewer.slack_id}>) to review {pr.html_url}",
                )
            session.commit()

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


__all__ = ["Bot"]
