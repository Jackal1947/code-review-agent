from .base import BaseAgent


class BugHunterAgent(BaseAgent):
    """专门用于发现代码 Bug 的智能体。"""

    def __init__(self):
        super().__init__(
            agent_type="bug",
            system_prompt="""你是一个 Bug 猎手智能体，专门负责在代码中发现严重缺陷。

重点关注领域：
- 空值 / 未定义值检查
- 边界条件
- 异常处理
- 并发问题
- 逻辑错误

你必须输出符合提供 Schema 的有效 JSON。不要在 JSON 之外输出任何文本。"""
        )

    @property
    def agent_type(self) -> str:
        return self._agent_type

    @property
    def system_prompt(self) -> str:
        return super().system_prompt

    def get_instructions(self) -> str:
        return """只关注 Bug，忽略代码风格和格式问题。

检查以下内容：
1. 访问前缺少空值/未定义值检查
2. 数组索引越界
3. 除以零
4. 未捕获的异常
5. 竞态条件
6. 条件判断中的逻辑错误

对于发现的每个 Bug，请提供符合 Schema 的 JSON 对象。"""
