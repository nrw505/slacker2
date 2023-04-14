import pytest

from threading import Thread
from unittest.mock import Mock


def test_bot_runs(bot):
    bot_thread = Thread(target=bot.run)
    bot_thread.start()

    # Wait for it to have started
    started = bot.wait_for_start(timeout=5)

    # If it didn't start in 2 sec, that's a fail
    assert started

    # Tell it to terminate
    bot.terminate()
    bot_thread.join(timeout=2)

    # If it didn't terminate in 2 sec, that's a fail
    assert not bot_thread.is_alive()


def test_logging_events(bot, capsys):
    request = Mock()
    request.type = "test"
    request.payload = {"test": "test"}
    bot.log_listener(bot.client, request)

    captured = capsys.readouterr()
    assert "request.type: test" in captured.out
    assert "request.payload: " in captured.out
