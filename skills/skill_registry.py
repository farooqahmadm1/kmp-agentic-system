import os
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

class KMPSkill:
    def __init__(self, name: str, description: str, content: str, triggers: List[str]):
        self.name = name
        self.description = description
        self.content = content
        self.triggers = triggers

class KMPSkillRegistry:
    """Discovers, indexes, and progressively injects modular KMP skills."""

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, KMPSkill] = {}
        self._load_skills()

    def _load_skills(self):
        if not self.skills_dir.exists():
            return
        for skill_folder in self.skills_dir.iterdir():
            if skill_folder.is_dir():
                skill_file = skill_folder / "SKILL.md"
                if skill_file.exists():
                    try:
                        text = skill_file.read_text(encoding="utf-8")
                        name = skill_folder.name
                        desc = ""
                        triggers = []
                        body = text

                        if text.startswith("---"):
                            parts = text.split("---", 2)
                            if len(parts) > 2:
                                if yaml is not None:
                                    meta = yaml.safe_load(parts[1]) or {}
                                    name = meta.get("name", name)
                                    desc = meta.get("description", "")
                                    triggers = meta.get("triggers", [])
                                body = parts[2].strip()

                        self.skills[name] = KMPSkill(
                            name=name,
                            description=desc,
                            content=body,
                            triggers=triggers
                        )
                    except Exception as e:
                        print(f"Warning: Failed to load skill {skill_folder}: {e}")

    def get_skill_content(self, skill_name: str) -> str:
        skill = self.skills.get(skill_name)
        return skill.content if skill else ""

    def get_skills_for_node(self, node_name: str) -> str:
        """Progressively injects only the skills relevant to the current LangGraph node."""
        node_map = {
            "compose_ui_node": ["compose-multiplatform-ui", "kmp-owasp-security"],
            "native_bridge_node": ["kmp-expect-actual", "kmp-native-interop", "kmp-owasp-security"],
            "core_domain_node": ["kmp-networking-storage", "kmp-owasp-security"],
            "gradle_build_node": ["kmp-gradle-catalog"],
            "diagnostic_node": ["kmp-build-diagnostics", "kmp-testing-mocking"],
            "guardrail_node": ["kmp-owasp-security"]
        }
        needed = node_map.get(node_name, [])
        blocks = []
        for name in needed:
            content = self.get_skill_content(name)
            if content:
                blocks.append(f"### [Active Domain Skill: {name}]\n{content}")
        return "\n\n".join(blocks)
