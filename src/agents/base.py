"""代码审查智能体的抽象基类。"""

from abc import ABC, abstractmethod
from typing import Any
import json

from src.llm_client import LLMReviewClient, ReviewPrompt


def agent_output_schema() -> dict[str, Any]:
    """返回智能体输出的 JSON Schema。"""
    return {
        "type": "object",
        "properties": {
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["bug", "quality", "security"]},
                        "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                        "file": {"type": "string"},
                        "line": {"type": "integer", "minimum": 1},
                        "description": {"type": "string"},
                        "suggestion": {"type": "string"},
                    },
                    "required": ["type", "severity", "confidence", "file", "line", "description", "suggestion"]
                }
            }
        },
        "required": ["issues"]
    }


class BaseAgent(ABC):
    """代码审查智能体的抽象基类。"""

    def __init__(self, agent_type: str, system_prompt: str):
        self._agent_type = agent_type
        self._system_prompt = system_prompt

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """返回该智能体的类型标识符。"""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """返回该智能体的系统提示词。"""
        pass

    @abstractmethod
    def get_instructions(self) -> str:
        """返回该智能体的操作指令。"""
        pass

    def build_prompt(self, context: dict[str, Any]) -> str:
        """根据给定上下文构建提示词。"""
        instructions = self.get_instructions()
        return f"{self.system_prompt}\n\n指令：{instructions}\n\n上下文：{context}"

    async def review(self, context: dict[str, Any]) -> list[dict]:
        """使用 LLM 审查代码并返回发现的问题。"""
        import logging
        logger = logging.getLogger(__name__)

        prompt = ReviewPrompt(
            system_prompt=self.system_prompt,
            instructions=self.get_instructions(),
            context=context
        )

        try:
            client = LLMReviewClient()
            response = await client.review(prompt, agent_output_schema())
        except Exception as e:
            logger.error(f"LLM API call failed: {type(e).__name__}: {e}")
            return []

        try:
            if isinstance(response, str):
                # Strip markdown code fences
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1] if "```" in cleaned else cleaned
                    # Remove language identifier if present (e.g., ```json)
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    elif cleaned.startswith("python"):
                        cleaned = cleaned[6:]
                cleaned = cleaned.strip()
                data = json.loads(cleaned)
            else:
                data = response

            if isinstance(data, dict):
                # Try different keys for issues
                issues = data.get("issues", [])
                if not issues:
                    # Try other common keys
                    for key in ["security_issues", "quality_issues", "bug_issues", "problems", "findings"]:
                        issues = data.get(key, [])
                        if issues:
                            break
                return self._normalize_issues(issues) if isinstance(issues, list) else []
            elif isinstance(data, list):
                return self._normalize_issues(data)
            return []
        except (json.JSONDecodeError, KeyError, Exception) as e:
            logger.error(f"Failed to parse LLM response: {type(e).__name__}: {e}")
            logger.error(f"Raw response: {response[:500] if isinstance(response, str) else response}")
            return []

    def _normalize_issues(self, issues: list) -> list:
        """Normalize issue field names to match the expected schema."""
        normalized = []
        severity_map = {
            "高": "high", "中": "medium", "低": "low",
            "高危": "high", "中危": "medium", "低危": "low",
            "high": "high", "medium": "medium", "low": "low",
            "High": "high", "Medium": "medium", "Low": "low",
        }
        type_map = {
            "SQL注入": "security", "SQL 注入": "security",
            "XSS": "security",
            "未验证输入": "security", "未经验证的用户输入": "security",
            "信息泄露": "security",
            "bug": "bug", "Bug": "bug",
            "quality": "quality", "Quality": "quality",
            "security": "security", "Security": "security",
        }

        for issue in issues:
            if isinstance(issue, dict):
                # Normalize severity
                severity = issue.get("severity", "medium")
                if isinstance(severity, str):
                    severity = severity_map.get(severity, "medium")

                # Normalize type
                issue_type = issue.get("type", self._agent_type)
                if isinstance(issue_type, str):
                    issue_type = type_map.get(issue_type, issue_type.lower())
                    # Fallback: if not in type_map, use the agent type if it's not a generic word
                    if issue_type not in ["bug", "quality", "security"]:
                        issue_type = self._agent_type

                # Map location to file if needed
                file = issue.get("file", issue.get("location", "unknown"))

                normalized.append({
                    "type": issue_type,
                    "severity": severity,
                    "confidence": issue.get("confidence", 80),
                    "file": file,
                    "line": issue.get("line", 1),
                    "description": issue.get("description", ""),
                    "suggestion": issue.get("suggestion", issue.get("fix", ""))
                })
        return normalized
