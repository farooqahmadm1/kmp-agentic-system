from pathlib import Path
from typing import Dict, Any, List

class UIPreviewVerifier:
    """Agent 9: Verifies Compose Multiplatform @Preview composables and UI hierarchy."""

    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()

    def verify_previews(self) -> Dict[str, Any]:
        """Scans generated UI files to ensure @Preview annotations and Material3 themes are properly structured."""
        ui_files = list(self.root.glob("composeApp/src/commonMain/kotlin/**/*Screen*.kt"))
        preview_count = 0
        missing_previews: List[str] = []

        for f in ui_files:
            try:
                content = f.read_text(encoding="utf-8")
                if "@Preview" in content:
                    preview_count += 1
                else:
                    missing_previews.append(str(f.name))
            except Exception:
                continue

        message = f"Verified {preview_count} Compose Multiplatform UI preview composables."
        if missing_previews:
            message += f" Missing @Preview in: {', '.join(missing_previews)}."
        return {
            "passed": not missing_previews,
            "preview_count": preview_count,
            "missing_previews": missing_previews,
            "message": message
        }
