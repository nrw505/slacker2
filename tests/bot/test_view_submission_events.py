import pytest
from unittest.mock import Mock


def test_non_interactive_event(bot):
    request = Mock()
    request.type = "events-api"
    request.payload = {}

    bot.view_submission_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_not_understood_event(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {"type": "not_understood"}

    bot.view_submission_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_unrecognised_view(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "view_submission",
        "view": {
            "callback_id": "unknown",
        },
        "trigger_id": "trigger",
        "user": {
            "id": "jane",
        },
    }

    bot.view_submission_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_view_submission_event_review_with_bad_pr_url(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "view_submission",
        "view": {
            "callback_id": "review-modal",
            "state": {
                "values": {
                    "pr": {
                        "pr_url": {
                            "value": "https://example.com/not_a_github_pr_url",
                        },
                    },
                    "channel": {
                        "channel": {"selected_channel": None},
                    },
                },
            },
        },
        "user": {
            "id": "jane",
        },
    }
    request.envelope_id = "test-envelope-id"

    bot.view_submission_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called()


def test_view_submission_event_review_with_good_pr_url(
    bot, default_slack_state, mocked_pr_url
):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "view_submission",
        "view": {
            "callback_id": "review-modal",
            "state": {
                "values": {
                    "pr": {
                        "pr_url": {
                            "value": mocked_pr_url,
                        },
                    },
                    "channel": {
                        "channel": {"selected_channel": "channel"},
                    },
                },
            },
        },
        "user": {
            "id": "jane",
        },
    }
    request.envelope_id = "test-envelope-id"

    bot.view_submission_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called()

    sent_messages = bot.client.web_client.sent_messages["channel"]
    assert f"Review request received for {mocked_pr_url}" in sent_messages
    assert "Assuming that Jane Janesdottir is nrw505 on github" in sent_messages
    assert f"Bob Bobsson (<@bob>) to review {mocked_pr_url}" in sent_messages


def test_view_submission_event_edit_github_username_with_username(
    bot, default_slack_state
):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "view_submission",
        "view": {
            "callback_id": "edit-github-username",
            "state": {
                "values": {
                    "github_username": {
                        "github_username": {
                            "value": "new123",
                        },
                    },
                },
            },
        },
        "user": {
            "id": "jane",
        },
    }
    request.envelope_id = "test-envelope-id"

    bot.view_submission_listener(bot.client, request)
    assert bot.client.web_client.views_published["jane"]


def test_view_submission_event_edit_github_username_with_bad_username(
    bot, default_slack_state, db_session
):

    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "view_submission",
        "view": {
            "callback_id": "edit-github-username",
            "state": {
                "values": {
                    "github_username": {
                        "github_username": {
                            "value": "%%!@#",
                        },
                    },
                },
            },
        },
        "user": {
            "id": "jane",
        },
    }
    request.envelope_id = "test-envelope-id"

    bot.view_submission_listener(bot.client, request)
    assert bot.client.web_client.views_published == {}
