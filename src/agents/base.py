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
        prompt = ReviewPrompt(
            system_prompt=self.system_prompt,
            instructions=self.get_instructions(),
            context=context
        )

        client = LLMReviewClient()
        response = await client.review(prompt, agent_output_schema())

        try:
            if isinstance(response, str):
                data = json.loads(response)
            else:
                data = response
            return data.get("issues", [])
        except (json.JSONDecodeError, KeyError):
            return []
