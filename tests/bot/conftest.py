import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from slacker.bot import Bot


@pytest.fixture
def dummy_socketmode_client(dummy_slack):
    dummy = Mock()
    dummy.web_client = dummy_slack
    dummy.send_socket_mode_response = Mock()
    dummy.socket_mode_request_listeners = []
    return dummy


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
    dummy_slack.set_user_presence("jane", "active")
    dummy_slack.set_channel_members("channel", ["bob", "jane"])


@pytest.fixture
def bot(
    dummy_socketmode_client,
    dummy_slack,
    dummy_github,
    db_session,
    broker,
):
    bot = Bot(
        "app_token",
        "bot_token",
        "github_token",
        # Bad DB URL so that we get errors if we try to use that instead of
        # the session factory we're about to inject
        "postgresql+psycopg2://bad_user:bad_password@localhost/bad_database",
    )
    bot.github = dummy_github
    bot.session_factory = lambda _engine: db_session
    bot.client = dummy_socketmode_client
    bot.broker = broker

    return bot
