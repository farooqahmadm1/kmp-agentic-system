from pathlib import Path, PurePosixPath
from typing import Iterable, Optional

class PathSandbox:
    """OWASP LLM06: Enforces strict sandboxed boundaries for all file I/O operations."""

    # Where agents may write, relative to the KMP root; a project can override it with `allowed_paths`.
    # A prefix ending in "/" matches a directory, anything else must match the whole path.
    DEFAULT_ALLOWED_PREFIXES = (
        "composeApp/src/commonMain/",
        "composeApp/src/androidMain/",
        "composeApp/src/iosMain/",
        "composeApp/src/desktopMain/",
        "composeApp/src/wasmJsMain/",
        "composeApp/src/commonTest/",
        "gradle/libs.versions.toml",
        "build.gradle.kts",
        "settings.gradle.kts",
        "composeApp/build.gradle.kts",
    )

    @classmethod
    def validate_safe_path(cls, target_path: str, allowed_root: str) -> Path:
        """Validates that target_path is strictly within allowed_root and prevents path traversal."""
        root_path = Path(allowed_root).resolve()

        # Resolve target path relative to root if relative, or absolute
        if Path(target_path).is_absolute():
            resolved = Path(target_path).resolve()
        else:
            resolved = (root_path / target_path).resolve()

        # Check boundary confinement
        try:
            resolved.relative_to(root_path)
        except ValueError:
            raise PermissionError(f"Security Alert: Path '{target_path}' attempts to escape sandbox boundary '{root_path}'!")

        return resolved

    @classmethod
    def is_source_file_allowed(cls, rel_path: str, allowed_prefixes: Optional[Iterable[str]] = None) -> bool:
        """Ensures agents only write to legitimate KMP project source sets."""
        rel = rel_path.replace("\\", "/")
        while rel.startswith("./"):
            rel = rel[2:]
        if rel.startswith("/") or ".." in PurePosixPath(rel).parts:
            return False
        for prefix in (allowed_prefixes or cls.DEFAULT_ALLOWED_PREFIXES):
            if rel.startswith(prefix) if prefix.endswith("/") else rel == prefix:
                return True
        return False
