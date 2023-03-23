import pytest

from slacker.bot import Bot


def test_bot_runs(db_connection, test_database_url):
    # db_connection is so that the test database can be created and torn down
    bot = Bot("app_token", "bot_token", "github_token", test_database_url)

    # TODO: figure out how to mock things so we can supply a dummy
    # SocketModeClient and WebClient when the bot calls the
    # constructors with dummy tokens

    # TODO: figure out how to clean the database after each test since
    # the bot is creating it's own engine and session instead of using
    # the db_session fixture which rolls back the transaction after
    # each test.
