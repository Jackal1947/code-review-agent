"""Tests for GitHub client."""

import pytest
from unittest.mock import MagicMock, patch
from src.github_client import GitHubClient
from src.models import Issue, ReviewResult


class TestGitHubClient:
    """Tests for GitHubClient class."""

    def test_init_with_token(self):
        """Check client initializes with explicit token."""
        client = GitHubClient(token="test-token-123")
        assert client.token == "test-token-123"
        assert client._client is None  # Not created until needed

    def test_init_without_token(self):
        """Check client initializes without token."""
        client = GitHubClient()
        assert client.token is None
        assert client._client is None

    def test_client_property_creates_instance(self):
        """Check client property creates Github instance lazily."""
        client = GitHubClient(token="test-token")
        with patch("src.github_client.Github") as mock_github:
            mock_github.return_value = MagicMock()
            _ = client.client
            mock_github.assert_called_once_with("test-token")

    def test_client_property_returns_same_instance(self):
        """Check client property returns the same instance on repeated calls."""
        client = GitHubClient(token="test-token")
        with patch("src.github_client.Github") as mock_github:
            mock_github.return_value = MagicMock()
            client1 = client.client
            client2 = client.client
            assert client1 is client2
            assert mock_github.call_count == 1

    def test_get_pull_request(self):
        """Check get_pull_request returns PR object."""
        client = GitHubClient(token="test-token")
        mock_pr = MagicMock()
        mock_client = MagicMock()
        mock_repo = MagicMock()
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        client._client = mock_client

        result = client.get_pull_request("owner", "repo", 42)

        mock_client.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_pull.assert_called_once_with(42)
        assert result == mock_pr

    def test_get_pr_diff(self):
        """Check get_pr_diff returns diff string."""
        client = GitHubClient(token="test-token")
        mock_diff = "diff --git a/test.py b/test.py"
        with patch.object(client, "get_pull_request") as mock_get_pr:
            mock_pr = MagicMock()
            mock_pr.diff.return_value = mock_diff
            mock_get_pr.return_value = mock_pr

            result = client.get_pr_diff("owner", "repo", 42)

            mock_pr.diff.assert_called_once()
            assert result == mock_diff

    def test_get_pr_files(self):
        """Check get_pr_files returns list of filenames."""
        client = GitHubClient(token="test-token")
        mock_files = [MagicMock(filename="test.py"), MagicMock(filename="main.py")]
        with patch.object(client, "get_pull_request") as mock_get_pr:
            mock_pr = MagicMock()
            mock_pr.get_files.return_value = mock_files
            mock_get_pr.return_value = mock_pr

            result = client.get_pr_files("owner", "repo", 42)

            assert result == ["test.py", "main.py"]

    def test_create_review_comment(self):
        """Check create_review_comment returns comment ID."""
        client = GitHubClient(token="test-token")
        mock_comment = MagicMock()
        mock_comment.id = 123
        with patch.object(client, "get_pull_request") as mock_get_pr:
            mock_pr = MagicMock()
            mock_pr.create_review_comment.return_value = mock_comment
            mock_get_pr.return_value = mock_pr

            result = client.create_review_comment("owner", "repo", 42, "body", "sha", "path", 10)

            mock_pr.create_review_comment.assert_called_once_with("body", "sha", "path", 10)
            assert result == "123"

    def test_get_reviews(self):
        """Check get_reviews returns list of review data."""
        client = GitHubClient(token="test-token")
        mock_review1 = MagicMock()
        mock_review1.user.login = "user1"
        mock_review1.state = "approved"
        mock_review1.body = "LGTM"
        mock_review2 = MagicMock()
        mock_review2.user.login = "user2"
        mock_review2.state = "commented"
        mock_review2.body = "Minor fix"
        with patch.object(client, "get_pull_request") as mock_get_pr:
            mock_pr = MagicMock()
            mock_pr.get_reviews.return_value = [mock_review1, mock_review2]
            mock_get_pr.return_value = mock_pr

            result = client.get_reviews("owner", "repo", 42)

            assert len(result) == 2
            assert result[0] == {"user": "user1", "state": "approved", "body": "LGTM"}
            assert result[1] == {"user": "user2", "state": "commented", "body": "Minor fix"}

    def test_create_issue_comment(self):
        """Check create_issue_comment returns comment ID."""
        client = GitHubClient(token="test-token")
        mock_comment = MagicMock()
        mock_comment.id = 456
        mock_client = MagicMock()
        mock_repo = MagicMock()
        mock_client.get_repo.return_value = mock_repo
        mock_issue = MagicMock()
        mock_issue.create_comment.return_value = mock_comment
        mock_repo.get_issue.return_value = mock_issue
        client._client = mock_client

        result = client.create_issue_comment("owner", "repo", 10, "comment body")

        mock_repo.get_issue.assert_called_once_with(10)
        mock_issue.create_comment.assert_called_once_with("comment body")
        assert result == "456"

    def test_post_review_result(self):
        """Check post_review_result posts comments for high/medium issues."""
        client = GitHubClient(token="test-token")
        issue1 = Issue(
            type="bug",
            severity="high",
            confidence=90,
            file="test.py",
            line=10,
            description="Bug description",
            suggestion="Fix it",
        )
        issue2 = Issue(
            type="quality",
            severity="low",
            confidence=50,
            file="test.py",
            line=20,
            description="Quality issue",
            suggestion="Improve it",
        )
        issue3 = Issue(
            type="security",
            severity="medium",
            confidence=80,
            file="auth.py",
            line=5,
            description="Security issue",
            suggestion="Secure it",
        )
        result = ReviewResult(
            issues=[issue1, issue2, issue3],
            summary="Overall summary",
            inline_comments=[issue1, issue3],
        )
        mock_commit = MagicMock()
        mock_commit.sha = "sha123"
        with patch.object(client, "get_pull_request") as mock_get_pr:
            mock_pr = MagicMock()
            mock_pr.get_head_commit.return_value = mock_commit
            mock_get_pr.return_value = mock_pr

            client.post_review_result("owner", "repo", 42, result)

            # Should post comments for high and medium severity (issue1 and issue3)
            assert mock_pr.create_review_comment.call_count == 2
            # Should post summary comment
            mock_pr.create_issue_comment.assert_called_once()
