import re
from typing import Tuple, List

class SecretRedactor:
    """OWASP LLM02: Scans and redacts API keys, credentials, and tokens before LLM dispatch."""

    PATTERNS = {
        "OpenAI/DeepSeek API Key": r"sk-[a-zA-Z0-9]{20,60}",
        "Generic Bearer Token": r"bearer\s+[a-zA-Z0-9_\-\.]{20,}",
        "Private Key Header": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "GitHub Personal Token": r"ghp_[a-zA-Z0-9]{36}",
        "Password in Code/URI": r"(password|passwd|pwd|secret)\s*[:=]\s*['\"][^\s'\"]{6,}['\"]",
        "Keystore Alias Password": r"storePassword\s*=\s*['\"][^\s'\"]+['\"]",
    }

    @classmethod
    def redact(cls, text: str) -> Tuple[str, List[str]]:
        """Redacts sensitive credentials from the input text, returning (redacted_text, detected_types)."""
        redacted_text = text
        detected = []

        for name, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, redacted_text, re.IGNORECASE)
            if matches:
                detected.append(name)
                redacted_text = re.sub(pattern, f"[REDACTED_{name.upper().replace(' ', '_')}]", redacted_text, flags=re.IGNORECASE)

        return redacted_text, detected
