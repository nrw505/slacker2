import pytest
from datetime import datetime

from slacker.model import User, Channel, UserChannelConfig, AssignedReview


def test_empty_app_view(bot, db_session):
    with db_session as session:
        jane = User(
            slack_id="jane",
            name="Jane Janesdottir",
            email="jane.janesdottir@example.com",
            github_username="jane",
        )
        session.add(jane)

        view = bot.app_home_view_for_user("jane")

    assert view["type"] == "home"
    assert len(view["blocks"]) == 8

    header_block = view["blocks"][0]
    assert header_block["type"] == "header"
    assert "Slacker" in header_block["text"]["text"]

    text_block = view["blocks"][1]
    assert text_block["type"] == "section"
    assert "No outstanding reviews" in text_block["text"]["text"]


def test_app_view_with_assigned_reviews(bot, db_session):
    with db_session as session:
        jane = User(
            slack_id="jane",
            name="Jane Janesdottir",
            email="jane.janesdottir@example.com",
            github_username="jane",
        )
        bob = User(
            slack_id="bob",
            name="Bob Bobsson",
            email="bob.bobsson@example.com",
            github_username="bob",
        )
        cheryl = User(
            slack_id="cheryl",
            name="Cheryl Cherylsdottir",
            email="cheryl.cherylsdottir@example.com",
            github_username=None,
        )
        channel = Channel(
            slack_id="channel", name="Test Channel", new_devs_are_reviewers=False
        )
        jane_in_channel = UserChannelConfig(
            user=jane, channel=channel, reviewer=True, notify_on_assignment=False
        )
        bob_in_channel = UserChannelConfig(
            user=bob, channel=channel, reviewer=False, notify_on_assignment=False
        )
        assignment_1 = AssignedReview(
            assignee=jane,
            requestor=bob,
            channel=channel,
            assigned_at=datetime.now(),
            pr_url="https://github.com/mock/mock/pull/1",
        )
        assignment_2 = AssignedReview(
            assignee=jane,
            requestor=bob,
            channel=channel,
            assigned_at=datetime.now(),
            acknowledged_at=datetime.now(),
            pr_url="https://github.com/mock/mock/pull/2",
        )
        assignment_3 = AssignedReview(
            assignee=jane,
            requestor=bob,
            channel=channel,
            assigned_at=datetime.now(),
            rerolled_at=datetime.now(),
            pr_url="https://github.com/mock/mock/pull/3",
        )
        assignment_4 = AssignedReview(
            assignee=jane,
            requestor=bob,
            channel=channel,
            assigned_at=datetime.now(),
            completed_at=datetime.now(),
            pr_url="https://github.com/mock/mock/pull/3",
        )
        session.add(jane)
        session.add(channel)
        session.add(cheryl)
        session.add(jane_in_channel)
        session.add(bob_in_channel)
        session.add(assignment_1)
        session.add(assignment_2)
        session.add(assignment_3)
        session.add(assignment_4)

        view1 = bot.app_home_view_for_user("jane")
        view2 = bot.app_home_view_for_user("bob")
        view3 = bot.app_home_view_for_user("cheryl")

    assert view1["type"] == "home"
    assert len(view1["blocks"]) == 13

    header_block = view1["blocks"][0]
    assert header_block["type"] == "header"
    assert "Slacker" in header_block["text"]["text"]

    assert view2["type"] == "home"

    assert view3["type"] == "home"

    # Right now I'm not so fussed by the content of the rest of the
    # blocks, just want to make sure we don't error generate them and
    # that we cover all the different rendering possibilities.
