"""团队规范 SKILL 加载器"""
import re
from pathlib import Path
from typing import Optional


class TeamSkillLoader:
    """加载并解析团队规范 SKILL 文件"""

    def __init__(self, skill_path: str = "team-rules-skill/SKILL.md"):
        self.skill_path = skill_path
        self._name: str = ""
        self._description: str = ""
        self._body: str = ""
        self._loaded: bool = False

    def load(self) -> bool:
        """加载 SKILL 文件，返回是否成功"""
        import logging
        logger = logging.getLogger(__name__)

        path = Path(self.skill_path)
        if not path.exists():
            logger.warning(f"Team skill file not found: {self.skill_path}")
            return False

        try:
            content = path.read_text(encoding="utf-8")
            self._parse_skill(content)
            self._loaded = True
            return True
        except Exception as e:
            logger.warning(f"Failed to parse skill file: {e}")
            return False

    def _parse_skill(self, content: str) -> None:
        """解析 SKILL 文件内容"""
        frontmatter_pattern = r"^---\n(.*?)\n---\n(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter = match.group(1)
            self._body = match.group(2).strip()
            self._parse_frontmatter(frontmatter)
        else:
            self._body = content.strip()

    def _parse_frontmatter(self, frontmatter: str) -> None:
        """解析 YAML frontmatter"""
        import yaml
        try:
            data = yaml.safe_load(frontmatter)
            self._name = data.get("name", "")
            self._description = data.get("description", "")
        except yaml.YAMLError:
            self._name = ""
            self._description = ""

    @property
    def name(self) -> str:
        """返回 SKILL 名称"""
        return self._name

    @property
    def description(self) -> str:
        """返回 SKILL 描述"""
        return self._description

    @property
    def body(self) -> str:
        """返回 SKILL body 内容（不含 frontmatter）"""
        return self._body

    @property
    def is_loaded(self) -> bool:
        """返回是否成功加载"""
        return self._loaded