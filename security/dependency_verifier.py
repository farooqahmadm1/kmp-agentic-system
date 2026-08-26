import re
from typing import Tuple, List

class DependencyVerifier:
    """OWASP LLM09: Anti-slopsquatting package validator for Gradle dependencies."""

    # Trusted package group prefixes commonly used in KMP
    TRUSTED_PREFIXES = (
        "org.jetbrains.kotlin",
        "org.jetbrains.compose",
        "org.jetbrains.kotlinx",
        "io.ktor",
        "androidx.room",
        "androidx.sqlite",
        "androidx.lifecycle",
        "androidx.navigation",
        "app.cash.sqldelight",
        "app.cash.turbine",
        "io.insert-koin",
        "io.coil-kt.coil3",
        "co.touchlab.skie",
        "io.mockative",
    )

    @classmethod
    def verify_dependency(cls, dep_string: str) -> Tuple[bool, str]:
        """Validates a Gradle dependency coordinate (e.g. 'io.ktor:ktor-client-core:3.0.0')."""
        clean = dep_string.strip().strip("'\"")
        parts = clean.split(":")
        
        if len(parts) < 2:
            return False, f"Invalid dependency format: '{dep_string}'. Expected 'group:artifact:version'."

        group = parts[0]
        
        # Check against trusted registry prefixes
        if any(group.startswith(prefix) for prefix in cls.TRUSTED_PREFIXES):
            return True, f"Verified trusted KMP dependency: {group}"

        # Flag untrusted third-party dependencies for review
        return False, f"Untrusted third-party dependency group: '{group}'. Requires manual verification against Maven Central."
