"""LLM Client for Code Review Agents."""
import os
import json
from typing import Any, Optional
from enum import Enum
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """支持的 LLM 提供商"""
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"


# 模型配置：(provider, 默认模型, 需要 api_key 环境变量)
LLM_MODELS = {
    # Anthropic
    "claude-opus-4-5": (LLMProvider.ANTHROPIC, "claude-opus-4-5", "ANTHROPIC_API_KEY"),
    "claude-sonnet-4-5": (LLMProvider.ANTHROPIC, "claude-sonnet-4-5", "ANTHROPIC_API_KEY"),
    "claude-opus-4-6": (LLMProvider.ANTHROPIC, "claude-opus-4-6", "ANTHROPIC_API_KEY"),
    "claude-sonnet-4-6": (LLMProvider.ANTHROPIC, "claude-sonnet-4-6", "ANTHROPIC_API_KEY"),
    "claude-haiku-4-5": (LLMProvider.ANTHROPIC, "claude-haiku-4-5", "ANTHROPIC_API_KEY"),
    # DeepSeek
    "deepseek-chat": (LLMProvider.DEEPSEEK, "deepseek-chat", "DEEPSEEK_API_KEY"),
    "deepseek-coder": (LLMProvider.DEEPSEEK, "deepseek-coder", "DEEPSEEK_API_KEY"),
    # OpenAI
    "gpt-4o": (LLMProvider.OPENAI, "gpt-4o", "OPENAI_API_KEY"),
    "gpt-4o-mini": (LLMProvider.OPENAI, "gpt-4o-mini", "OPENAI_API_KEY"),
    "gpt-4-turbo": (LLMProvider.OPENAI, "gpt-4-turbo", "OPENAI_API_KEY"),
}


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
    """通用的 LLM 客户端，支持多种模型提供商。

    使用方式：
    1. 默认配置（环境变量或 claude-opus-4-5）：
       client = LLMReviewClient()

    2. 指定模型：
       client = LLMReviewClient(model="deepseek-chat")
       client = LLMReviewClient(model="gpt-4o")

    3. 自定义提供商实例：
       client = LLMReviewClient(model="deepseek-chat", provider=LLMProvider.DEEPSEEK)
    """

    def __init__(
        self,
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        # 确定模型和提供商
        model = model or os.environ.get("LLM_MODEL", "claude-opus-4-5")

        if provider:
            self.provider = provider
            self.model = model
        elif model in LLM_MODELS:
            self.provider, self.model, self._required_env = LLM_MODELS[model]
        else:
            # 未知模型，默认用 OpenAI兼容接口
            self.provider = LLMProvider.OPENAI
            self.model = model
            self._required_env = "OPENAI_API_KEY"

        # 获取 API key
        self.api_key = api_key or os.environ.get(f"{self.provider.upper()}_API_KEY")
        self.base_url = base_url or os.environ.get(f"{self.provider.upper()}_BASE_URL")

        if not self.api_key:
            raise ValueError(f"Missing API key: set {self._required_env} environment variable")

        # 创建客户端
        self._client = self._create_client()

    def _create_client(self) -> BaseChatModel:
        """根据提供商创建对应的客户端"""
        if self.provider == LLMProvider.ANTHROPIC:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=self.model, api_key=self.api_key)

        elif self.provider == LLMProvider.DEEPSEEK:
            from langchain_deepseek import ChatDeepSeek
            kwargs = {"model": self.model, "api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            return ChatDeepSeek(**kwargs)

        elif self.provider == LLMProvider.OPENAI:
            from langchain_openai import ChatOpenAI
            kwargs = {"model": self.model, "api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            return ChatOpenAI(**kwargs)

        raise ValueError(f"Unsupported provider: {self.provider}")

    async def review(self, prompt: ReviewPrompt, output_schema: dict) -> Any:
        """Call LLM with structured output."""
        messages = prompt.build_messages()
        response = await self._client.ainvoke(messages)
        return response.content
