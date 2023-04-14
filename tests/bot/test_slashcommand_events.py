import pytest
from unittest.mock import Mock


def test_non_interactive_event(bot):
    request = Mock()
    request.type = "events-api"
    request.payload = {}

    bot.review_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_not_understood_event(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {"type": "not_understood"}

    bot.review_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_slash_command_trigger_event(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "shortcut",
        "callback_id": "review",
        "trigger_id": "trigger",
    }
    request.envelope_id = "test-envelope-id"

    bot.review_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called()
    assert "trigger" in bot.client.web_client.views_opened


def test_view_submission_event_with_bad_pr_url(bot):
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
    }
    request.envelope_id = "test-envelope-id"

    bot.review_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called()


def test_view_submission_event_with_good_pr_url(
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

    bot.review_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called()

    sent_messages = bot.client.web_client.sent_messages["channel"]
    assert f"Review request received for {mocked_pr_url}" in sent_messages
    assert "Assuming that Jane Janesdottir is nrw505 on github" in sent_messages
    assert f"Bob Bobsson (<@bob>) to review {mocked_pr_url}" in sent_messages
