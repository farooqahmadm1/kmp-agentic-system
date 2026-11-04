import html
import re

_DELIMITERS = re.compile(r"</?\s*(user_task_specification|untrusted_source_file)\b[^>]*>", re.IGNORECASE)

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

        # Enforce XML instruction boundaries. Only the delimiter tags are neutralised (so the prompt
        # can't close its own wrapper); escaping everything would mangle Kotlin generics like List<User>.
        cleaned = _DELIMITERS.sub(lambda m: html.escape(m.group(0)), cleaned)
        return f"<user_task_specification>\n{cleaned}\n</user_task_specification>"

    @classmethod
    def wrap_untrusted_code(cls, code: str, filename: str) -> str:
        """Wraps untrusted code chunks in boundary tags to prevent indirect prompt injection."""
        code = _DELIMITERS.sub(lambda m: html.escape(m.group(0)), code).replace("]]>", "]]]]><![CDATA[>")
        return (f'<untrusted_source_file name="{html.escape(filename, quote=True)}">\n'
                f'<![CDATA[\n{code}\n]]>\n</untrusted_source_file>')
