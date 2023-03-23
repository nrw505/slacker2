import pytest
import os
from sqlalchemy import create_engine, Engine, Connection
from sqlalchemy.orm import Session
from typing import Generator
from unittest.mock import Mock
from slacker.data_broker import DataBroker
from slacker.model import Base


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    if test_db_url is None:  # pragma: no cover
        # only here to detect when the dev environment is not set up
        # properly, won't ever happen in CI
        raise RuntimeError("TEST_DATABASE_URL is not set in environment")
    return create_engine(test_db_url)


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

    def __init__(self):
        self.channel_members = {}
        self.users = {}
        self.presence = {}

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


@pytest.fixture
def dummy_slack() -> DummySlack:
    return DummySlack()


@pytest.fixture
def broker(dummy_slack) -> DataBroker:
    return DataBroker(dummy_slack)
