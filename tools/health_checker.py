import urllib.request
import json
from typing import Dict, Any, Tuple

from config import config

class HealthChecker:
    """Pre-flight detector for Ollama daemon, VRAM, and DeepSeek API connectivity."""

    @classmethod
    def check_ollama(cls) -> Tuple[bool, str, list]:
        """Checks if Ollama is running and lists installed models."""
        url = f"{config.ollama_base_url.rstrip('/')}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KMPAgent/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", [])]
                    has_model = any(config.local_model in m for m in models)
                    msg = f"Ollama is running. Model '{config.local_model}' is {'available' if has_model else 'NOT found'}."
                    return True, msg, models
        except Exception as e:
            return False, f"Ollama connection failed ({e}). Please ensure 'ollama serve' is running.", []
        return False, "Ollama check returned unexpected status.", []

    @classmethod
    def check_all(cls) -> Dict[str, Any]:
        ollama_ok, ollama_msg, models = cls.check_ollama()
        has_deepseek = bool(config.deepseek_api_key)
        return {
            "ollama_active": ollama_ok,
            "ollama_message": ollama_msg,
            "ollama_models": models,
            "deepseek_configured": has_deepseek,
            "daily_token_limit": config.daily_token_limit,
            "all_systems_go": ollama_ok or has_deepseek
        }
