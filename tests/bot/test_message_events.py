import pytest
from unittest.mock import Mock


def test_non_events_api_event(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {}

    bot.message_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_malformed_event(bot):
    request = Mock()
    request.type = "events_api"
    request.payload = {}

    bot.message_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_non_message_event(bot):
    request = Mock()
    request.type = "events_api"
    request.payload = {"event": {"type": "something else"}}

    bot.message_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_random_message_event(bot):
    request = Mock()
    request.type = "events_api"
    request.payload = {"event": {"type": "message", "text": "random text"}}

    bot.message_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called_once()


def test_review_with_bad_url_message_event(bot):
    request = Mock()
    request.type = "events_api"
    request.payload = {
        "event": {
            "type": "message",
            "text": "!review https://example.com/not_a_github_pr",
        }
    }

    bot.message_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called_once()


def test_review_with_good_url_message_event(bot, default_slack_state, mocked_pr_url):
    request = Mock()
    request.type = "events_api"
    request.payload = {
        "event": {
            "type": "message",
            "user": "jane",
            "channel": "channel",
            "text": f"!review {mocked_pr_url}",
        }
    }

    bot.message_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called_once()
    sent_messages = bot.client.web_client.sent_messages["channel"]
    assert f"Review request received for {mocked_pr_url}" in sent_messages
    assert "Assuming that Jane Janesdottir is nrw505 on github" in sent_messages
    assert f"Bob Bobsson (<@bob>) to review {mocked_pr_url}" in sent_messages


def test_review_with_no_reviewer_message_event(bot, default_slack_state, mocked_pr_url):
    bot.client.web_client.set_user_presence("bob", "away")

    request = Mock()
    request.type = "events_api"
    request.payload = {
        "event": {
            "type": "message",
            "user": "jane",
            "channel": "channel",
            "text": f"!review {mocked_pr_url}",
        }
    }

    bot.message_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called_once()
    sent_messages = bot.client.web_client.sent_messages["channel"]
    assert f"Review request received for {mocked_pr_url}" in sent_messages
    assert "Assuming that Jane Janesdottir is nrw505 on github" in sent_messages
    assert f"No eligible reviewers for {mocked_pr_url}" in sent_messages
