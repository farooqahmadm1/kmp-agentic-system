from pathlib import Path
from typing import Dict, Optional
from security.path_sandbox import PathSandbox
from state import KMPFileSpec

class KMPWorkspaceManager:
    """Manages reading and writing source files to the isolated KMP workspace."""

    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()

    def write_file(self, file_spec: KMPFileSpec) -> str:
        """Safely writes a file to the workspace while enforcing path boundary sandbox."""
        safe_path = PathSandbox.validate_safe_path(file_spec.file_path, str(self.root))
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(file_spec.content, encoding="utf-8")
        return f"Successfully wrote {file_spec.file_path}"

    def read_file(self, rel_path: str) -> Optional[str]:
        safe_path = PathSandbox.validate_safe_path(rel_path, str(self.root))
        if safe_path.exists():
            return safe_path.read_text(encoding="utf-8")
        return None
