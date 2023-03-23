import pytest
from unittest.mock import Mock

from slacker.actions.assign_review import AssignReview


@pytest.fixture
def default_slack_state(dummy_slack):
    dummy_slack.set_user(
        "bob",
        {"real_name": "Bob Bobsson", "profile": {"email": "bob.bobsson@example.com"}},
    )
    dummy_slack.set_user(
        "jane",
        {
            "real_name": "Jane Janesdottir",
            "profile": {"email": "jane.janesdottir@example.com"},
        },
    )
    dummy_slack.set_user_presence("bob", "active")
    dummy_slack.set_user_presence("jane", "away")
    dummy_slack.set_channel_members("channel", ["bob", "jane"])


def test_no_eligible_reviewers(broker, default_slack_state, db_session):
    mock_pr = Mock()
    mock_pr.user.login = "bob"
    mock_pr.html_url = "https://github.com/mock/mock/pull/1"

    with db_session as session:
        action = AssignReview(broker)
        result = action.perform(session, "bob", "channel", mock_pr)

    assert result.successful == False
    assert (
        "No eligible reviewers for https://github.com/mock/mock/pull/1" in result.errors
    )
    assert "Assuming that Bob Bobsson is bob on github" in result.messages
    assert result.reviewer is None
