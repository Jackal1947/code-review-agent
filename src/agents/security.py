from .base import BaseAgent


class SecurityAgent(BaseAgent):
    """专门用于发现安全问题的智能体。"""

    def __init__(self):
        super().__init__(
            agent_type="security",
            system_prompt="""你是一个安全检查智能体，专门负责发现安全漏洞。

重点关注领域：
- SQL 注入
- 权限检查
- 敏感数据暴露
- 认证/授权问题
- 输入验证
- XSS 漏洞

你必须输出符合提供 Schema 的有效 JSON。不要在 JSON 之外输出任何文本。"""
        )

    def get_instructions(self) -> str:
        return """只关注安全问题，忽略 Bug 和代码质量。

检查以下内容：
1. SQL 注入漏洞
2. 缺少认证/授权检查
3. 硬编码的凭据或密钥
4. 未经验证的用户输入
5. 信息泄露
6. 不安全的反序列化
7. XSS 漏洞

对于发现的每个问题，请提供符合 Schema 的 JSON 对象。"""
