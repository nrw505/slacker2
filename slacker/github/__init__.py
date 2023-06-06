import os
import re
from github import Github
from github.PullRequest import PullRequest

PR_RE = re.compile("https://github.com/([^/]*)/([^/]*)/pull/([0-9]+)")
USERNAME_RE = re.compile("^[a-z0-9](?:[a-z0-9]|-(?=[a-z0-9])){0,38}$")


class InvalidURLError(ValueError):
    pass


class GitHub:
    client: Github

    def __init__(self, token: str) -> None:
        self.client = Github(token)

    def valid_pr_url(self, url: str) -> bool:
        match = PR_RE.match(url)
        return match is not None

    def valid_username(self, username: str) -> bool:
        match = USERNAME_RE.match(username)
        return match is not None

    def pr(self, url: str) -> PullRequest:
        match = PR_RE.match(url)
        if match is None:
            raise InvalidURLError("Not a valid GitHub PR URL")
        repo_name = match[1] + "/" + match[2]
        pr_num = int(match[3])
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_num)
        return pr


__all__ = ["GitHub", "InvalidURLError", "PullRequest"]
