import os
from pathlib import Path
from typing import Dict, Any, List

try:
    import yaml
except ImportError:
    yaml = None

CONFIG_PATH = Path("kmp_agent_config.yaml")

class AppConfig:
    def __init__(self, config_dict: Dict[str, Any]):
        self._raw = config_dict
        
        # Models configuration
        models = config_dict.get("models", {})
        self.cloud_provider = models.get("cloud_provider", "deepseek").lower()
        
        # Models per provider
        self.deepseek_model = models.get("deepseek_model", "deepseek-chat")
        self.anthropic_model = models.get("anthropic_model", "claude-3-5-sonnet-latest")
        self.gemini_model = models.get("gemini_model", "gemini-2.0-flash")
        
        # API Keys from environment
        self.deepseek_api_key = os.getenv(models.get("deepseek_api_key_env", "DEEPSEEK_API_KEY"), "")
        self.anthropic_api_key = os.getenv(models.get("anthropic_api_key_env", "ANTHROPIC_API_KEY"), "")
        self.gemini_api_key = os.getenv(models.get("gemini_api_key_env", "GEMINI_API_KEY"), os.getenv("GOOGLE_API_KEY", ""))

        self.daily_token_limit = int(models.get("daily_token_limit", 150000))
        self.local_provider = models.get("local_provider", "ollama")
        self.local_model = models.get("local_model", "qwen2.5-coder:14b")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", models.get("ollama_base_url", "http://localhost:11434"))

        # KMP target matrix
        kmp = config_dict.get("kmp", {})
        self.target_platforms: List[str] = kmp.get("target_platforms", ["android", "ios", "desktop", "wasmJs"])
        self.ui_framework = kmp.get("ui_framework", "compose_multiplatform_m3")
        self.di_framework = kmp.get("di_framework", "koin")

        # Guardrails
        guardrails = config_dict.get("guardrails", {})
        self.hitl_plan_approval = bool(guardrails.get("hitl_plan_approval", True))
        self.hitl_diff_review = bool(guardrails.get("hitl_diff_review", True))
        self.owasp_enforcement = bool(guardrails.get("owasp_keychain_keystore_enforcement", True))
        self.max_self_healing_iterations = int(guardrails.get("max_self_healing_iterations", 5))

        # Paths
        paths = config_dict.get("paths", {})
        self.sessions_dir = Path(paths.get("sessions_dir", ".sessions"))
        self.worktrees_dir = Path(paths.get("worktrees_dir", ".worktrees"))
        self.logs_dir = Path(paths.get("logs_dir", ".logs"))
        self.skills_dir = Path(paths.get("skills_dir", "skills"))

        # Ensure essential directories exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.skills_dir.mkdir(parents=True, exist_ok=True)

def load_config() -> AppConfig:
    data = {}
    if CONFIG_PATH.exists() and yaml is not None:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = {}
    return AppConfig(data)

config = load_config()
