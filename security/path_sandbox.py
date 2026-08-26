from pathlib import Path

class PathSandbox:
    """OWASP LLM06: Enforces strict sandboxed boundaries for all file I/O operations."""

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
    def is_source_file_allowed(cls, rel_path: str) -> bool:
        """Ensures agents only write to legitimate KMP project source sets."""
        allowed_prefixes = (
            "composeApp/src/commonMain",
            "composeApp/src/androidMain",
            "composeApp/src/iosMain",
            "composeApp/src/desktopMain",
            "composeApp/src/wasmJsMain",
            "composeApp/src/commonTest",
            "gradle/",
            "build.gradle.kts",
            "settings.gradle.kts",
            "composeApp/build.gradle.kts"
        )
        return any(rel_path.startswith(prefix) for prefix in allowed_prefixes)
