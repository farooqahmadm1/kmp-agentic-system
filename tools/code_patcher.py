from pathlib import Path
from typing import Optional

class CodePatcher:
    """Applies surgical diffs or file updates to resolved compiler error sites."""

    @classmethod
    def apply_patch(cls, full_file_path: str, new_content: str) -> bool:
        path = Path(full_file_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new_content, encoding="utf-8")
            return True
        except Exception:
            return False
