import pytest

from slacker.github import GitHub, InvalidURLError


@pytest.fixture
def dummy_github() -> GitHub:
    return GitHub("dummy-token")


def test_creation(dummy_github):
    assert dummy_github is not None


def test_valid_pr_url(dummy_github):
    assert dummy_github.valid_pr_url("https://example.com") is False
    assert dummy_github.valid_pr_url("https://github.com/user/repo/pull/1234") is True
    assert dummy_github.valid_pr_url("https://github.com/user/repo/pull/XYZ") is False
    assert dummy_github.valid_pr_url("https://github.com/user/repo/issue/1234") is False
    assert dummy_github.valid_pr_url("https://github.com/user/repo/pulls") is False


def test_pr_with_invalid_url(dummy_github):
    with pytest.raises(InvalidURLError):
        dummy_github.pr("https://example.com")


def test_pr_with_valid_url(dummy_github, requests_mock):
    requests_mock.get(
        "https://api.github.com:443/repos/nrw505/slacker2",
        text="""{
  "id": 588425690,
  "node_id": "R_kgDOIxKp2g",
  "name": "slacker2",
  "full_name": "nrw505/slacker2",
  "private": false,
  "owner": {
    "login": "nrw505",
    "id": 8898943,
    "node_id": "MDQ6VXNlcjg4OTg5NDM=",
    "avatar_url": "https://avatars.githubusercontent.com/u/8898943?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/nrw505",
    "html_url": "https://github.com/nrw505",
    "followers_url": "https://api.github.com/users/nrw505/followers",
    "following_url": "https://api.github.com/users/nrw505/following{/other_user}",
    "gists_url": "https://api.github.com/users/nrw505/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/nrw505/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/nrw505/subscriptions",
    "organizations_url": "https://api.github.com/users/nrw505/orgs",
    "repos_url": "https://api.github.com/users/nrw505/repos",
    "events_url": "https://api.github.com/users/nrw505/events{/privacy}",
    "received_events_url": "https://api.github.com/users/nrw505/received_events",
    "type": "User",
    "site_admin": false
  },
  "html_url": "https://github.com/nrw505/slacker2",
  "description": null,
  "fork": false,
  "url": "https://api.github.com/repos/nrw505/slacker2",
  "forks_url": "https://api.github.com/repos/nrw505/slacker2/forks",
  "keys_url": "https://api.github.com/repos/nrw505/slacker2/keys{/key_id}",
  "collaborators_url": "https://api.github.com/repos/nrw505/slacker2/collaborators{/collaborator}",
  "teams_url": "https://api.github.com/repos/nrw505/slacker2/teams",
  "hooks_url": "https://api.github.com/repos/nrw505/slacker2/hooks",
  "issue_events_url": "https://api.github.com/repos/nrw505/slacker2/issues/events{/number}",
  "events_url": "https://api.github.com/repos/nrw505/slacker2/events",
  "assignees_url": "https://api.github.com/repos/nrw505/slacker2/assignees{/user}",
  "branches_url": "https://api.github.com/repos/nrw505/slacker2/branches{/branch}",
  "tags_url": "https://api.github.com/repos/nrw505/slacker2/tags",
  "blobs_url": "https://api.github.com/repos/nrw505/slacker2/git/blobs{/sha}",
  "git_tags_url": "https://api.github.com/repos/nrw505/slacker2/git/tags{/sha}",
  "git_refs_url": "https://api.github.com/repos/nrw505/slacker2/git/refs{/sha}",
  "trees_url": "https://api.github.com/repos/nrw505/slacker2/git/trees{/sha}",
  "statuses_url": "https://api.github.com/repos/nrw505/slacker2/statuses/{sha}",
  "languages_url": "https://api.github.com/repos/nrw505/slacker2/languages",
  "stargazers_url": "https://api.github.com/repos/nrw505/slacker2/stargazers",
  "contributors_url": "https://api.github.com/repos/nrw505/slacker2/contributors",
  "subscribers_url": "https://api.github.com/repos/nrw505/slacker2/subscribers",
  "subscription_url": "https://api.github.com/repos/nrw505/slacker2/subscription",
  "commits_url": "https://api.github.com/repos/nrw505/slacker2/commits{/sha}",
  "git_commits_url": "https://api.github.com/repos/nrw505/slacker2/git/commits{/sha}",
  "comments_url": "https://api.github.com/repos/nrw505/slacker2/comments{/number}",
  "issue_comment_url": "https://api.github.com/repos/nrw505/slacker2/issues/comments{/number}",
  "contents_url": "https://api.github.com/repos/nrw505/slacker2/contents/{+path}",
  "compare_url": "https://api.github.com/repos/nrw505/slacker2/compare/{base}...{head}",
  "merges_url": "https://api.github.com/repos/nrw505/slacker2/merges",
  "archive_url": "https://api.github.com/repos/nrw505/slacker2/{archive_format}{/ref}",
  "downloads_url": "https://api.github.com/repos/nrw505/slacker2/downloads",
  "issues_url": "https://api.github.com/repos/nrw505/slacker2/issues{/number}",
  "pulls_url": "https://api.github.com/repos/nrw505/slacker2/pulls{/number}",
  "milestones_url": "https://api.github.com/repos/nrw505/slacker2/milestones{/number}",
  "notifications_url": "https://api.github.com/repos/nrw505/slacker2/notifications{?since,all,participating}",
  "labels_url": "https://api.github.com/repos/nrw505/slacker2/labels{/name}",
  "releases_url": "https://api.github.com/repos/nrw505/slacker2/releases{/id}",
  "deployments_url": "https://api.github.com/repos/nrw505/slacker2/deployments",
  "created_at": "2023-01-13T04:44:02Z",
  "updated_at": "2023-01-13T04:45:01Z",
  "pushed_at": "2023-02-10T03:53:04Z",
  "git_url": "git://github.com/nrw505/slacker2.git",
  "ssh_url": "git@github.com:nrw505/slacker2.git",
  "clone_url": "https://github.com/nrw505/slacker2.git",
  "svn_url": "https://github.com/nrw505/slacker2",
  "homepage": null,
  "size": 66,
  "stargazers_count": 0,
  "watchers_count": 0,
  "language": "Python",
  "has_issues": true,
  "has_projects": true,
  "has_downloads": true,
  "has_wiki": true,
  "has_pages": false,
  "has_discussions": false,
  "forks_count": 0,
  "mirror_url": null,
  "archived": false,
  "disabled": false,
  "open_issues_count": 0,
  "license": null,
  "allow_forking": true,
  "is_template": false,
  "web_commit_signoff_required": false,
  "topics": [],
  "visibility": "public",
  "forks": 0,
  "open_issues": 0,
  "watchers": 0,
  "default_branch": "main",
  "permissions": {
    "admin": true,
    "maintain": true,
    "push": true,
    "triage": true,
    "pull": true
  },
  "temp_clone_token": "",
  "allow_squash_merge": true,
  "allow_merge_commit": true,
  "allow_rebase_merge": true,
  "allow_auto_merge": false,
  "delete_branch_on_merge": false,
  "allow_update_branch": false,
  "use_squash_pr_title_as_default": false,
  "squash_merge_commit_message": "COMMIT_MESSAGES",
  "squash_merge_commit_title": "COMMIT_OR_PR_TITLE",
  "merge_commit_message": "PR_TITLE",
  "merge_commit_title": "MERGE_MESSAGE",
  "security_and_analysis": {
    "secret_scanning": {
      "status": "disabled"
    },
    "secret_scanning_push_protection": {
      "status": "disabled"
    }
  },
  "network_count": 0,
  "subscribers_count": 1
}""",
    )
    result = dummy_github.pr("https://github.com/nrw505/slacker2/pull/1")
