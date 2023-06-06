import pytest
from datetime import datetime
from unittest.mock import Mock

from slacker.model import User, Channel, UserChannelConfig, AssignedReview


@pytest.fixture
def preloaded_assignment_id(db_session, mocked_pr_url):
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
        cheryl = User(
            slack_id="cheryl",
            name="Cheryl Chernobyl",
            email="cheryl.chernobyl@example.com",
            github_username="nrw505",
        )
        channel = Channel(
            slack_id="channel", name="Test Channel", new_devs_are_reviewers=True
        )
        assignment = AssignedReview(
            assignee=jane,
            requestor=cheryl,
            channel=channel,
            assigned_at=datetime.now(),
            acknowledged_at=None,
            rerolled_at=None,
            completed_at=None,
            pr_url=mocked_pr_url,
        )
        session.add(bob)
        session.add(assignment)

        # Make sure we get ids from actually inserting them
        session.flush()
        assignment_id = assignment.id

    return assignment_id


def test_non_block_actions_event(bot):
    request = Mock()
    request.type = "events_api"
    request.payload = {}

    bot.block_actions_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_not_understood_event(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {"type": "not_understood"}

    bot.block_actions_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_acknowledge_assignment_event(bot, db_session, preloaded_assignment_id):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "jane"},
        "actions": [
            {
                "action_id": "assignment-acknowledge",
                "value": str(preloaded_assignment_id),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    assert "jane" in bot.client.web_client.views_published

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.acknowledged_at is not None


def test_acknowledge_assignment_event_from_wrong_person(
    bot, db_session, preloaded_assignment_id
):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "bob"},
        "actions": [
            {
                "action_id": "assignment-acknowledge",
                "value": str(preloaded_assignment_id),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    assert bot.client.web_client.views_published == {}

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.acknowledged_at is None


def test_acknowledge_assignment_event_for_nonexistent_assignment(
    bot, db_session, preloaded_assignment_id
):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "jane"},
        "actions": [
            {
                "action_id": "assignment-acknowledge",
                "value": str(preloaded_assignment_id + 1000),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    assert bot.client.web_client.views_published == {}

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.acknowledged_at is None


def test_reviewed_assignment_event(bot, db_session, preloaded_assignment_id):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "jane"},
        "actions": [
            {
                "action_id": "assignment-reviewed",
                "value": str(preloaded_assignment_id),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    assert "jane" in bot.client.web_client.views_published

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.completed_at is not None


def test_reviewed_assignment_event_from_wrong_person(
    bot, db_session, preloaded_assignment_id
):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "bob"},
        "actions": [
            {
                "action_id": "assignment-reviewed",
                "value": str(preloaded_assignment_id),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    assert bot.client.web_client.views_published == {}

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.completed_at is None


def test_reviewed_assignment_event_for_nonexistent_assignment(
    bot, db_session, preloaded_assignment_id
):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "jane"},
        "actions": [
            {
                "action_id": "assignment-reviewed",
                "value": str(preloaded_assignment_id + 1000),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    assert bot.client.web_client.views_published == {}

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.completed_at is None


def test_reroll_assignment_event(
    bot, default_slack_state, db_session, preloaded_assignment_id, mocked_pr_url
):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "jane"},
        "actions": [
            {
                "action_id": "assignment-reroll",
                "value": str(preloaded_assignment_id),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    messages = bot.client.web_client.sent_messages["channel"]
    assert f"Rerolling {mocked_pr_url}" in messages
    assert f"Bob Bobsson (<@bob>) to review {mocked_pr_url}" in messages
    assert "jane" in bot.client.web_client.views_published

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.rerolled_at is not None


def test_reroll_assignment_where_nobody_is_eligible_event(
    bot, default_slack_state, db_session, preloaded_assignment_id, mocked_pr_url
):
    with db_session as session:
        # Bob isn't a reviewer. Jane has already been assigned. Cheryl
        # requested the review. So no eligible reviewers left.
        bob = bot.broker.fetch_user_by_slack_id_or_create_from_slack(session, "bob")
        channel = bot.broker.fetch_channel_by_slack_id_or_create_from_slack(
            session, "channel"
        )
        bob_in_channel = bot.broker.fetch_or_create_channel_config_for_user_in_channel(
            session, bob, channel
        )
        bob_in_channel.reviewer = False
        session.flush()

    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "jane"},
        "actions": [
            {
                "action_id": "assignment-reroll",
                "value": str(preloaded_assignment_id),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    messages = bot.client.web_client.sent_messages["channel"]
    assert f"Rerolling {mocked_pr_url}" in messages
    assert f"No eligible reviewers for {mocked_pr_url}" in messages
    assert "jane" in bot.client.web_client.views_published

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.rerolled_at is None


def test_reroll_assignment_event_from_wrong_person(
    bot, default_slack_state, db_session, preloaded_assignment_id, mocked_pr_url
):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "bob"},
        "actions": [
            {
                "action_id": "assignment-reroll",
                "value": str(preloaded_assignment_id),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    assert "channel" not in bot.client.web_client.sent_messages
    assert bot.client.web_client.views_published == {}

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.rerolled_at is None


def test_reroll_assignment_event_for_nonexistent_assignment(
    bot, default_slack_state, db_session, preloaded_assignment_id, mocked_pr_url
):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "jane"},
        "actions": [
            {
                "action_id": "assignment-reroll",
                "value": str(preloaded_assignment_id + 1000),
            },
        ],
        "trigger_id": "1",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)

    assert "channel" not in bot.client.web_client.sent_messages
    assert bot.client.web_client.views_published == {}

    reloaded = bot.broker.fetch_assignment_for_id(db_session, preloaded_assignment_id)
    assert reloaded.rerolled_at is None


def test_edit_user_github_username(bot, default_slack_state, db_session):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "block_actions",
        "user": {"id": "jane"},
        "actions": [
            {"action_id": "edit-user-github-username", "value": "1"},
        ],
        "trigger_id": "trigger",
    }
    request.envelope_id = "test-envelope-id"

    bot.block_actions_listener(bot.client, request)
    assert bot.client.web_client.views_opened["trigger"]
