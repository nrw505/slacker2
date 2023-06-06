import pytest
from unittest.mock import Mock


def test_non_interactive_event(bot):
    request = Mock()
    request.type = "events-api"
    request.payload = {}

    bot.shortcut_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_not_understood_event(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {"type": "not_understood"}

    bot.shortcut_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_not_called()


def test_not_unrecognised_shortcut(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "shortcut",
        "callback_id": "unknown",
        "trigger_id": "trigger",
    }

    bot.shortcut_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called()


def test_slash_command_trigger_event(bot):
    request = Mock()
    request.type = "interactive"
    request.payload = {
        "type": "shortcut",
        "callback_id": "review",
        "trigger_id": "trigger",
    }
    request.envelope_id = "test-envelope-id"

    bot.shortcut_listener(bot.client, request)

    bot.client.send_socket_mode_response.assert_called()
    assert "trigger" in bot.client.web_client.views_opened
