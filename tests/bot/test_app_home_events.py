import pytest
from unittest.mock import Mock


def test_non_events_api_event(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {}

    bot.app_home_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_not_understood_event(bot):
    request = Mock()
    request.type = "events_api"
    request.payload = {"event": {"type": "not_understood"}}

    bot.app_home_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_app_home_opened_event(bot, default_slack_state):
    request = Mock()
    request.type = "events_api"
    request.payload = {
        "event": {
            "type": "app_home_opened",
            "user": "bob",
        }
    }

    bot.app_home_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called()
    assert "bob" in bot.client.web_client.views_published
