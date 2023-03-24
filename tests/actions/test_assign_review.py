import pytest
from unittest.mock import Mock
from datetime import datetime

from slacker.model import User, Channel, UserChannelConfig, AssignedReview
from slacker.actions.assign_review import AssignReview


@pytest.fixture
def default_slack_state(dummy_slack):
    dummy_slack.set_user(
        "bob",
        {"real_name": "Bob Bobsson", "profile": {"email": "bob.bobsson@example.com"}},
    )
    dummy_slack.set_user(
        "jane",
        {
            "real_name": "Jane Janesdottir",
            "profile": {"email": "jane.janesdottir@example.com"},
        },
    )
    dummy_slack.set_user_presence("bob", "active")
    dummy_slack.set_user_presence("jane", "away")
    dummy_slack.set_channel_members("channel", ["bob", "jane"])


@pytest.fixture
def mock_pr():
    mock_pr = Mock()
    mock_pr.user.login = "bob"
    mock_pr.html_url = "https://github.com/mock/mock/pull/1"
    return mock_pr


def test_no_eligible_reviewers(broker, default_slack_state, db_session, mock_pr):

    with db_session as session:
        action = AssignReview(broker)
        result = action.perform(session, "bob", "channel", mock_pr)

    assert not result.successful
    assert (
        "No eligible reviewers for https://github.com/mock/mock/pull/1" in result.errors
    )
    assert "Assuming that Bob Bobsson is bob on github" in result.messages
    assert result.reviewer is None


def test_with_eligible_reviewer(
    broker, default_slack_state, dummy_slack, db_session, mock_pr
):
    dummy_slack.set_user_presence("jane", "active")

    with db_session as session:
        jane = User(
            slack_id="jane",
            name="Jane Janesdottir",
            email="jane.janesdottir@example.com",
            github_username="jane",
        )
        bob = User(
            slack_id="bob",
            name="Bob Bobsson",
            email="bob.bobsson@example.com",
            github_username="bob",
        )
        session.add(jane)
        session.add(bob)

        action = AssignReview(broker)
        result = action.perform(session, "bob", "channel", mock_pr)

    assert result.successful
    assert "Assuming that Bob Bobsson is bob on github" not in result.messages
    assert result.reviewer.slack_id == "jane"


def test_jane_exists_but_is_not_a_reviewer(
    broker, default_slack_state, dummy_slack, db_session, mock_pr
):
    dummy_slack.set_user_presence("jane", "active")
    with db_session as session:
        jane = User(
            slack_id="jane",
            name="Jane Janesdottir",
            email="jane.janesdottir@example.com",
            github_username="jane",
        )
        bob = User(
            slack_id="bob",
            name="Bob Bobsson",
            email="bob.bobsson@example.com",
            github_username="bob",
        )
        channel = Channel(
            slack_id="channel",
            name="Test Channel",
            new_devs_are_reviewers=False,
        )
        jane_in_channel = UserChannelConfig(
            user=jane, channel=channel, reviewer=False, notify_on_assignment=False
        )
        session.add(jane)
        session.add(bob)
        session.add(channel)
        session.add(jane_in_channel)

        action = AssignReview(broker)
        result = action.perform(session, "bob", "channel", mock_pr)

    assert not result.successful
    assert (
        "No eligible reviewers for https://github.com/mock/mock/pull/1" in result.errors
    )
    assert result.reviewer is None


def test_jane_has_already_been_assigned_a_review(
    broker, default_slack_state, dummy_slack, db_session, mock_pr
):
    dummy_slack.set_user_presence("jane", "active")
    with db_session as session:
        jane = User(
            slack_id="jane",
            name="Jane Janesdottir",
            email="jane.janesdottir@example.com",
            github_username="jane",
        )
        bob = User(
            slack_id="bob",
            name="Bob Bobsson",
            email="bob.bobsson@example.com",
            github_username="bob",
        )
        channel = Channel(
            slack_id="channel",
            name="Test Channel",
            new_devs_are_reviewers=True,
        )
        existing_assignment = AssignedReview(
            user=jane,
            channel=channel,
            assigned_at=datetime.now(),
            pr_url=mock_pr.html_url,
        )
        session.add(jane)
        session.add(bob)
        session.add(channel)
        session.add(existing_assignment)

        action = AssignReview(broker)
        result = action.perform(session, "bob", "channel", mock_pr)

    assert not result.successful
    assert (
        "No eligible reviewers for https://github.com/mock/mock/pull/1" in result.errors
    )
    assert result.reviewer is None
