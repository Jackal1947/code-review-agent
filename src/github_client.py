"""GitHub client for Code Review Agent."""
from typing import Optional, List
from github import Github, GithubException
from github.Auth import Token as GitHubToken
from src.models import DiffChunk, Issue, ReviewResult


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token. If None, uses GITHUB_TOKEN env var.
        """
        self.token = token
        self._client: Optional[Github] = None

    @property
    def client(self) -> Github:
        """Get or create the GitHub client instance."""
        if self._client is None:
            token = self.token
            self._client = Github(token) if token else Github()
        return self._client

    def get_pull_request(self, owner: str, repo: str, pr_number: int):
        """Get a pull request by owner, repo, and PR number.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            PullRequest object.

        Raises:
            GithubException: If PR not found.
        """
        return self.client.get_repo(f"{owner}/{repo}").get_pull(pr_number)

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Get the diff for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            Diff as a string.
        """
        pr = self.get_pull_request(owner, repo, pr_number)
        return pr.diff()

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[str]:
        """Get list of files changed in a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of filenames.
        """
        pr = self.get_pull_request(owner, repo, pr_number)
        return [f.filename for f in pr.get_files()]

    def create_review_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
    ) -> str:
        """Create a review comment on a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.
            body: Comment body.
            commit_id: Commit SHA.
            path: File path.
            line: Line number.

        Returns:
            The created comment's ID.
        """
        pr = self.get_pull_request(owner, repo, pr_number)
        comment = pr.create_review_comment(body, commit_id, path, line)
        return str(comment.id)

    def get_reviews(self, owner: str, repo: str, pr_number: int) -> List[dict]:
        """Get all reviews for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of review data dictionaries.
        """
        pr = self.get_pull_request(owner, repo, pr_number)
        return [
            {
                "user": r.user.login,
                "state": r.state,
                "body": r.body,
            }
            for r in pr.get_reviews()
        ]

    def create_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> str:
        """Create a comment on an issue.

        Args:
            owner: Repository owner.
            repo: Repository name.
            issue_number: Issue number.
            body: Comment body.

        Returns:
            The created comment's ID.
        """
        repo_obj = self.client.get_repo(f"{owner}/{repo}")
        comment = repo_obj.get_issue(issue_number).create_comment(body)
        return str(comment.id)

    def post_review_result(self, owner: str, repo: str, pr_number: int, result: ReviewResult) -> None:
        """Post a review result as comments to a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.
            result: ReviewResult to post.
        """
        pr = self.get_pull_request(owner, repo, pr_number)

        for issue in result.issues:
            if issue.severity in ("high", "medium"):
                body = f"**[{issue.type.upper()}][{issue.severity.upper()}]** {issue.description}\n\n**Suggestion:** {issue.suggestion}"
                try:
                    pr.as_review_comments()[0]  # Check if review exists
                except GithubException:
                    pass
                # Post as single comment for now
                pr.create_review_comment(
                    body,
                    pr.get_head_commit().sha,
                    issue.file,
                    issue.line,
                )

        if result.summary:
            pr.create_issue_comment(f"**Code Review Summary:**\n{result.summary}")
