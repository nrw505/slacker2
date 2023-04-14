import pytest

import os
from sqlalchemy import create_engine, Engine, Connection
from sqlalchemy.orm import Session
from typing import Generator, Callable
from unittest.mock import Mock
from slacker.data_broker import DataBroker
from slacker.model import Base
from slacker.github import GitHub
from tests.fixtures import *


@pytest.fixture(scope="session")
def test_database_url() -> str:
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    if test_db_url is None:  # pragma: no cover
        # only here to detect when the dev environment is not set up
        # properly, won't ever happen in CI
        raise RuntimeError("TEST_DATABASE_URL is not set in environment")
    return test_db_url


@pytest.fixture(scope="session")
def db_engine(test_database_url) -> Engine:
    return create_engine(test_database_url)


@pytest.fixture(scope="session")
def db_connection(db_engine: Engine) -> Generator[Connection, None, None]:
    connection = db_engine.connect()

    transaction = connection.begin()
    Base.metadata.create_all(bind=connection)
    transaction.commit()

    yield connection

    transaction = connection.begin()
    Base.metadata.drop_all(bind=connection)
    transaction.commit()


@pytest.fixture
def db_session(db_connection: Connection) -> Generator[Session, None, None]:
    transaction = db_connection.begin()
    yield Session(db_connection)
    transaction.rollback()


class DummySlack:
    channel_members: dict[str, list[str]]
    users: dict[str, dict[str, str]]
    presence: dict[str, str]
    sent_messages: dict[str, list[str]]
    views_opened: dict[str, dict]
    views_published: dict[str, dict]

    def __init__(self):
        self.channel_members = {}
        self.users = {}
        self.presence = {}
        self.sent_messages = {}
        self.views_opened = {}
        self.views_published = {}

    def set_user(self, user_id: str, user: dict[str, str]):
        self.users[user_id] = user

    def set_user_presence(self, user_id: str, presence: str):
        self.presence[user_id] = presence

    def set_channel_members(self, channel_id, user_list: list[str]):
        self.channel_members[channel_id] = user_list

    def users_info(self, user: str):
        return {"user": self.users[user]}

    def users_getPresence(self, user: str):
        return {"presence": self.presence[user]}

    def conversations_info(self, channel: str):
        return {"channel": {"name": f"test channel {channel}"}}

    def conversations_members(self, channel: str):
        for user in self.channel_members[channel]:
            yield {"members": [user]}

    def chat_postMessage(self, channel: str, text: str):
        if channel not in self.sent_messages:
            self.sent_messages[channel] = []
        self.sent_messages[channel].append(text)

    def views_open(self, trigger_id: str, view: dict):
        self.views_opened[trigger_id] = view

    def views_publish(self, user_id: str, view: dict):
        self.views_published[user_id] = view


@pytest.fixture
def dummy_slack() -> DummySlack:
    return DummySlack()


@pytest.fixture
def broker(dummy_slack) -> DataBroker:
    return DataBroker(dummy_slack)


@pytest.fixture
def dummy_github() -> GitHub:
    return GitHub("dummy-token")
