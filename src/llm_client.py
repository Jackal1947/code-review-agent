"""LLM Client for Code Review Agents."""
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel


def _load_env():
    """加载 .env 环境变量文件"""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


# 加载 .env 文件
_load_env()


class ReviewPrompt(BaseModel):
    """Structured prompt for code review."""
    system_prompt: str
    instructions: str
    context: dict[str, Any]

    def context_repr(self) -> str:
        return f"File: {self.context.get('file', 'unknown')}\n\nCode:\n{self.context.get('code', '')}"

    def build_messages(self) -> list:
        return [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"{self.instructions}\n\n{self.context_repr()}")
        ]


class LLMReviewClient:
    """DeepSeek LLM 客户端，用于代码审查。

    使用方式：
    1. 环境变量配置（默认）：
       export DEEPSEEK_API_KEY=sk-...

    2. 代码中指定：
       client = LLMReviewClient(api_key="sk-...")
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

        if not self.api_key:
            raise ValueError("Missing API key: set DEEPSEEK_API_KEY environment variable or .env file")

        self._client = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
        )

    async def review(self, prompt: ReviewPrompt, output_schema: dict) -> Any:
        """调用 LLM 审查代码."""
        messages = prompt.build_messages()
        response = await self._client.ainvoke(messages)
        return response.content
