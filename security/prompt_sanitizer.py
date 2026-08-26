import html
import re

class PromptSanitizer:
    """OWASP LLM01: Defends against prompt injection and jailbreak payloads."""

    SUSPICIOUS_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"disregard\s+system\s+prompt",
        r"you\s+are\s+now\s+in\s+dan\s+mode",
        r"system\s*:\s*override",
        r"rm\s+-rf\s+/",
        r"DROP\s+DATABASE",
    ]

    @classmethod
    def sanitize_user_prompt(cls, prompt: str) -> str:
        """Wraps user prompts in strict delimiter boundaries and flags injection attempts."""
        cleaned = prompt.strip()
        
        # Check for obvious injection heuristics
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned = re.sub(pattern, "[FLAGGED_INJECTION_ATTEMPT]", cleaned, flags=re.IGNORECASE)

        # Enforce XML instruction boundaries
        return f"<user_task_specification>\n{html.escape(cleaned)}\n</user_task_specification>"

    @classmethod
    def wrap_untrusted_code(cls, code: str, filename: str) -> str:
        """Wraps untrusted code chunks in boundary tags to prevent indirect prompt injection."""
        return f'<untrusted_source_file name="{filename}">\n<![CDATA[\n{code}\n]]>\n</untrusted_source_file>'
