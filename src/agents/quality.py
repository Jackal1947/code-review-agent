from .base import BaseAgent


class CodeQualityAgent(BaseAgent):
    """专门用于发现代码质量问题的智能体。"""

    def __init__(self):
        super().__init__(
            agent_type="quality",
            system_prompt="""你是一个代码质量智能体，专门负责发现代码质量问题。

重点关注领域：
- 可读性
- 代码重复
- 设计问题
- 命名规范
- 注释质量

你必须输出符合提供 Schema 的有效 JSON。不要在 JSON 之外输出任何文本。"""
        )

    def get_instructions(self) -> str:
        return """只关注代码质量问题，忽略 Bug（由 BugHunter 负责）和代码风格。

检查以下内容：
1. 可以提取的重复代码
2. 过长或过于复杂的函数
3. 变量/函数命名不当
4. 缺少或不清晰的注释
5. 模块间的紧耦合
6. SOLID 原则违反

如果提示中包含了项目目录结构和依赖关系信息，请利用这些信息：
- 检查新增的符号（类/函数）是否与项目中已有符号存在命名冲突
- 检查新增模块是否放在了正确的目录/包中，是否符合项目现有的分层结构
- 检查是否存在循环依赖的风险

对于发现的每个问题，请提供符合 Schema 的 JSON 对象。"""
