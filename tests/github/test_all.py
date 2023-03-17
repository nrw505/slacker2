import pytest

from slacker.github import GitHub, InvalidURLError


def test_creation(dummy_github: GitHub):
    assert dummy_github is not None


def test_valid_pr_url(dummy_github: GitHub):
    assert dummy_github.valid_pr_url("https://example.com") is False
    assert dummy_github.valid_pr_url("https://github.com/user/repo/pull/1234") is True
    assert dummy_github.valid_pr_url("https://github.com/user/repo/pull/XYZ") is False
    assert dummy_github.valid_pr_url("https://github.com/user/repo/issue/1234") is False
    assert dummy_github.valid_pr_url("https://github.com/user/repo/pulls") is False


def test_pr_with_invalid_url(dummy_github: GitHub):
    with pytest.raises(InvalidURLError):
        dummy_github.pr("https://example.com")


def test_pr_with_valid_url(dummy_github: GitHub, mocked_pr_url: str):
    pr = dummy_github.pr(mocked_pr_url)

    assert pr.user.login == "nrw505"
