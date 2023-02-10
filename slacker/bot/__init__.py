import logging
import re
import random
from datetime import datetime

from typing import Dict, List

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

from .user_presence_cache import UserPresenceCache

from slacker.model import User, Channel, UserChannelConfig, AssignedReview


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
        self.user_presence_cache = UserPresenceCache(client.web_client)

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

            errors: Dict[str, str] = {}

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
            requesting_user = self.get_user_by_slack_id(session, requestor)
            if requesting_user.github_username is None:
                requesting_user.github_username = pr.user.login
                session.add(requesting_user)
                self.send_text_to_channel(
                    channel,
                    f"Assuming that {requesting_user.name} is {pr.user.login} on github",
                )
            potential_reviewers = self.calculate_eligible_reviewers_in_channel(
                session, channel
            )
            potential_reviewers = [
                user
                for user in potential_reviewers
                if user != requesting_user and user.github_username != pr.user.login
            ]

            if not any(potential_reviewers):
                self.send_text_to_channel(
                    channel, f"No eligible reviewers for {pr_url}"
                )
                return

            reviewer = random.choice(potential_reviewers)
            db_channel = self.get_channel_by_slack_id(session, channel)
            assign = AssignedReview(
                user=reviewer,
                channel=db_channel,
                pr_url=pr_url,
                assigned_at=datetime.now(),
            )
            session.add(assign)
            session.commit()

            self.send_text_to_channel(
                channel, f"{reviewer.name} (<@{reviewer.slack_id}>) to review {pr_url}"
            )

    def calculate_eligible_reviewers_in_channel(
        self, session: Session, channel: str
    ) -> List[User]:
        channel_members = []
        for page in self.client.web_client.conversations_members(channel=channel):
            channel_members += page["members"]
        print(f"channel_members = {channel_members}")
        active_members = [
            member
            for member in channel_members
            if self.user_presence_cache.getUserPresence(member)
        ]
        print(f"active_members = {active_members}")
        db_users = [
            self.get_user_by_slack_id(session, member) for member in active_members
        ]
        print(f"db_users = {db_users}")
        db_channel = self.get_channel_by_slack_id(session, channel)
        print(f"db_channel = {db_channel}")
        channel_configs = [
            self.get_channel_config_for_user(session, user, db_channel)
            for user in db_users
        ]
        print(f"channel_configs = {channel_configs}")
        reviewers = [config.user for config in channel_configs if config.reviewer]
        print(f"reviewers = {reviewers}")
        return reviewers

    def get_user_by_slack_id(self, session: Session, slack_id: str) -> User:
        statement = select(User).where(User.slack_id == slack_id)
        user = session.scalars(statement).one_or_none()

        if user is None:
            real_name = "Unknown"
            email = None

            response = self.client.web_client.users_info(user=slack_id)
            slack_data = response.get("user")
            print(f"slack_data = {slack_data}")
            if slack_data is not None:
                real_name = slack_data["real_name"]
                email = slack_data["profile"]["email"]

            user = User(
                slack_id=slack_id,
                name=real_name,
                email=email,
            )
            session.add(user)
            session.commit()
        return user

    def get_channel_by_slack_id(self, session: Session, slack_id: str) -> Channel:
        statement = select(Channel).where(Channel.slack_id == slack_id)
        channel = session.scalars(statement).one_or_none()

        if channel is None:
            name = "unknown"

            response = self.client.web_client.conversations_info(channel=slack_id)
            slack_data = response.get("channel")
            if slack_data is not None:
                name = slack_data["name"]

            channel = Channel(
                slack_id=slack_id,
                name=name,
                new_devs_are_reviewers=True,
            )
            session.add(channel)
            session.commit()
        return channel

    def get_channel_config_for_user(
        self, session: Session, user: User, channel: Channel
    ) -> UserChannelConfig:
        statement = (
            select(UserChannelConfig)
            .where(UserChannelConfig.channel_id == channel.id)
            .where(UserChannelConfig.user_id == user.id)
        )
        config = session.scalars(statement).one_or_none()

        if config is None:
            config = UserChannelConfig(
                user=user,
                channel=channel,
                reviewer=channel.new_devs_are_reviewers,
                notify_on_assignment=False,
            )
            session.add(config)
            session.commit()

        return config

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
