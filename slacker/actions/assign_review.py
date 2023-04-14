from typing import Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass
from datetime import datetime
import random

from slacker.github import PullRequest
from slacker.model import User, Channel, AssignedReview
from slacker.data_broker import DataBroker


@dataclass
class AssignReviewResult:
    messages: list[str]
    reviewer: Optional[User]


class AssignReview:
    broker: DataBroker

    def __init__(self, broker: DataBroker):
        self.broker = broker

    def perform(
        self,
        session: Session,
        requestor_slack_id: str,
        channel_slack_id: str,
        pr: PullRequest,
    ) -> AssignReviewResult:
        result = AssignReviewResult(messages=[], reviewer=None)

        requesting_user = self.broker.fetch_user_by_slack_id_or_create_from_slack(
            session, requestor_slack_id
        )
        channel = self.broker.fetch_channel_by_slack_id_or_create_from_slack(
            session, channel_slack_id
        )

        if requesting_user.github_username is None:
            requesting_user.github_username = pr.user.login
            session.add(requesting_user)
            result.messages.append(
                f"Assuming that {requesting_user.name} is {pr.user.login} on github"
            )

        potential_reviewers = self.calculate_eligible_reviewers_in_channel(
            session, channel
        )
        existing_assignments = self.broker.fetch_assignments_for_pr_url(
            session, pr.html_url
        )
        assigned_users = [assignment.assignee for assignment in existing_assignments]

        potential_reviewers = [
            user
            for user in potential_reviewers
            if user != requesting_user
            and user.github_username != pr.user.login
            and user not in assigned_users
        ]

        if not any(potential_reviewers):
            result.messages.append(f"No eligible reviewers for {pr.html_url}")
            return result

        reviewer = random.choice(potential_reviewers)

        assign = AssignedReview(
            assignee=reviewer,
            requestor=requesting_user,
            channel=channel,
            pr_url=pr.html_url,
            assigned_at=datetime.now(),
        )
        session.add(assign)

        result.reviewer = reviewer
        return result

    def calculate_eligible_reviewers_in_channel(
        self, session: Session, channel: Channel
    ) -> list[User]:
        channel_members = self.broker.fetch_slack_user_ids_from_channel(channel)
        print(f"channel_members = {channel_members}")
        active_members = [
            member
            for member in channel_members
            if self.broker.get_user_presence_for_slack_id(member)
        ]
        print(f"active_members = {active_members}")
        users = [
            self.broker.fetch_user_by_slack_id_or_create_from_slack(session, member)
            for member in active_members
        ]
        print(f"users = {users}")
        channel_configs = [
            self.broker.fetch_or_create_channel_config_for_user_in_channel(
                session, user, channel
            )
            for user in users
        ]
        print(f"channel_configs = {channel_configs}")
        reviewers = [config.user for config in channel_configs if config.reviewer]
        print(f"reviewers = {reviewers}")
        return reviewers
