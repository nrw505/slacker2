from typing import Sequence, Optional
from slack_sdk.web import WebClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from slacker.user_presence_cache import UserPresenceCache
from slacker.user_presence_provider import SlackClientUserPresenceProvider
from slacker.model import User, Channel, UserChannelConfig, AssignedReview


class DataBroker:
    slack: WebClient

    def __init__(self, slack: WebClient):
        self.slack = slack
        self.user_presence_cache = UserPresenceCache(
            SlackClientUserPresenceProvider(slack)
        )

    def fetch_user_by_slack_id_or_create_from_slack(
        self, session: Session, slack_id: str
    ) -> User:
        statement = select(User).where(User.slack_id == slack_id)
        user = session.scalars(statement).one_or_none()

        if user is None:
            real_name = "Unknown"
            email = None

            response = self.slack.users_info(user=slack_id)
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

        return user

    def fetch_channel_by_slack_id_or_create_from_slack(
        self, session: Session, slack_id: str
    ) -> Channel:
        statement = select(Channel).where(Channel.slack_id == slack_id)
        channel = session.scalars(statement).one_or_none()

        if channel is None:
            name = "unknown"

            response = self.slack.conversations_info(channel=slack_id)
            slack_data = response.get("channel")
            if slack_data is not None:
                name = slack_data["name"]

            channel = Channel(
                slack_id=slack_id,
                name=name,
                new_devs_are_reviewers=True,
            )
            session.add(channel)

        return channel

    def fetch_or_create_channel_config_for_user_in_channel(
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

        return config

    def fetch_assignments_for_pr_url(
        self, session: Session, pr_url: str
    ) -> Sequence[AssignedReview]:
        statement = select(AssignedReview).where(AssignedReview.pr_url == pr_url)
        return session.scalars(statement).all()

    def fetch_active_assignments_for_slack_user_id(
        self, session: Session, slack_user_id: str
    ) -> Sequence[AssignedReview]:
        statement = (
            select(AssignedReview)
            .join(User.assigned_reviews)
            .where(User.slack_id == slack_user_id)
            .where(AssignedReview.completed_at == None)
            .order_by(AssignedReview.assigned_at)
        )
        return session.scalars(statement).all()

    def fetch_assignment_for_id(
        self, session: Session, id: int
    ) -> Optional[AssignedReview]:
        statement = select(AssignedReview).where(AssignedReview.id == id)
        return session.scalars(statement).one_or_none()

    def fetch_slack_user_ids_from_channel(self, channel: Channel) -> list[str]:
        channel_members = []
        for page in self.slack.conversations_members(channel=channel.slack_id):
            channel_members += page["members"]
        return channel_members

    def get_user_presence_for_slack_id(self, slack_user_id: str) -> bool:
        return self.user_presence_cache.getUserPresence(slack_user_id)


__all__ = ["DataBroker"]
