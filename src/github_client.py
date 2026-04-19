"""GitHub 客户端，用于代码审查智能体。"""
from typing import Optional, List
from github import Github, GithubException
from github.Auth import Token as GitHubToken
from src.models import DiffChunk, Issue, ReviewResult


class GitHubClient:
    """与 GitHub API 交互的客户端。"""

    def __init__(self, token: Optional[str] = None):
        """初始化 GitHub 客户端。

        Args:
            token: GitHub 个人访问令牌。若为 None，则使用环境变量 GITHUB_TOKEN。
        """
        self.token = token
        self._client: Optional[Github] = None

    @property
    def client(self) -> Github:
        """获取或创建 GitHub 客户端实例。"""
        if self._client is None:
            token = self.token
            self._client = Github(token) if token else Github()
        return self._client

    def get_pull_request(self, owner: str, repo: str, pr_number: int):
        """通过仓库所有者、仓库名和 PR 编号获取 Pull Request。

        Args:
            owner: 仓库所有者。
            repo: 仓库名称。
            pr_number: Pull Request 编号。

        Returns:
            PullRequest 对象。

        Raises:
            GithubException: 若 PR 不存在则抛出异常。
        """
        return self.client.get_repo(f"{owner}/{repo}").get_pull(pr_number)

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """获取 Pull Request 的差异内容。

        Args:
            owner: 仓库所有者。
            repo: 仓库名称。
            pr_number: Pull Request 编号。

        Returns:
            字符串格式的差异内容。
        """
        import requests
        headers = {
            "Authorization": f"token {self.token}" if self.token else "",
            "Accept": "application/vnd.github.v3.diff"
        }
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        # When using application/vnd.github.v3.diff, the diff is in the response body directly
        return resp.text

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[str]:
        """获取 Pull Request 中变更的文件列表。

        Args:
            owner: 仓库所有者。
            repo: 仓库名称。
            pr_number: Pull Request 编号。

        Returns:
            文件名列表。
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
        """在 Pull Request 上创建审查评论。

        Args:
            owner: 仓库所有者。
            repo: 仓库名称。
            pr_number: Pull Request 编号。
            body: 评论内容。
            commit_id: 提交 SHA。
            path: 文件路径。
            line: 行号。

        Returns:
            已创建评论的 ID。
        """
        pr = self.get_pull_request(owner, repo, pr_number)
        comment = pr.create_review_comment(body, commit_id, path, line)
        return str(comment.id)

    def get_reviews(self, owner: str, repo: str, pr_number: int) -> List[dict]:
        """获取 Pull Request 的所有审查记录。

        Args:
            owner: 仓库所有者。
            repo: 仓库名称。
            pr_number: Pull Request 编号。

        Returns:
            审查数据字典列表。
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
        """在 Issue 上创建评论。

        Args:
            owner: 仓库所有者。
            repo: 仓库名称。
            issue_number: Issue 编号。
            body: 评论内容。

        Returns:
            已创建评论的 ID。
        """
        repo_obj = self.client.get_repo(f"{owner}/{repo}")
        comment = repo_obj.get_issue(issue_number).create_comment(body)
        return str(comment.id)

    def post_review_result(self, owner: str, repo: str, pr_number: int, result: ReviewResult) -> None:
        """将审查结果以评论形式发布到 Pull Request。

        Args:
            owner: 仓库所有者。
            repo: 仓库名称。
            pr_number: Pull Request 编号。
            result: 要发布的 ReviewResult 对象。
        """
        pr = self.get_pull_request(owner, repo, pr_number)

        for issue in result.issues:
            if issue.severity in ("high", "medium"):
                body = f"**[{issue.type.upper()}][{issue.severity.upper()}]** {issue.description}\n\n**建议：** {issue.suggestion}"
                try:
                    pr.as_review_comments()[0]  # 检查审查是否存在
                except GithubException:
                    pass
                # 暂时以单条评论形式发布
                pr.create_review_comment(
                    body,
                    pr.get_head_commit().sha,
                    issue.file,
                    issue.line,
                )

        if result.summary:
            pr.create_issue_comment(f"**代码审查摘要：**\n{result.summary}")
