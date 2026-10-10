import time
from typing import List, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from config import config
from models.token_budget import TokenBudgetManager
from security.secret_redactor import SecretRedactor
from memory.trajectory_log import log_event, preview

class HybridModelRouter:
    """Dynamic Multi-Cloud LLM Gateway (Claude, Gemini, DeepSeek, Ollama).

    Providers are tried in order: `cloud_provider`, then each of `fallback_providers`,
    then local Ollama.
    """

    def __init__(self, task_id: str = "default"):
        self.task_id = task_id
        self.budget_mgr = TokenBudgetManager(
            db_path=str(config.sessions_dir / "token_budget.db"),
            daily_token_limit=config.daily_token_limit
        )

        # 1. Local Ollama Provider (Fallback / Offline)
        try:
            from langchain_ollama import ChatOllama
            self.local_llm = ChatOllama(
                base_url=config.ollama_base_url,
                model=config.local_model,
                temperature=0.2
            )
        except Exception:
            self.local_llm = None

        # 2. Cloud Provider Chain
        self.cloud_chain = []  # list of (provider_name, model_name, llm)
        for name in [config.cloud_provider, *config.fallback_providers]:
            if any(n == name for n, _, _ in self.cloud_chain):
                continue
            try:
                entry = self._build_provider(name)
                if entry:
                    self.cloud_chain.append(entry)
            except Exception as e:
                print(f"Notice: Cloud provider {name} initialization: {e}")

        self.active_provider_name = self.cloud_chain[0][0] if self.cloud_chain else "ollama"

    @staticmethod
    def _build_provider(name: str):
        # Subscription-backed providers (no API key; use the logged-in CLI account)
        if name == "claude_code":
            from models.subscription_cli import ClaudeCodeCLI
            return name, config.claude_code_model, ClaudeCodeCLI(config.claude_code_model, config.cli_timeout)
        if name == "gemini_cli":
            from models.subscription_cli import GeminiCLI
            return name, config.gemini_cli_model, GeminiCLI(config.gemini_cli_model, config.cli_timeout)

        # API-key providers
        if name == "anthropic" and config.anthropic_api_key:
            from langchain_anthropic import ChatAnthropic
            return name, config.anthropic_model, ChatAnthropic(
                model_name=config.anthropic_model,
                api_key=config.anthropic_api_key,
                temperature=0.2
            )
        if name == "gemini" and config.gemini_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return name, config.gemini_model, ChatGoogleGenerativeAI(
                model=config.gemini_model,
                google_api_key=config.gemini_api_key,
                temperature=0.2
            )
        if name == "deepseek" and config.deepseek_api_key:
            from langchain_openai import ChatOpenAI
            return name, config.deepseek_model, ChatOpenAI(
                model=config.deepseek_model,
                api_key=config.deepseek_api_key,
                base_url="https://api.deepseek.com/v1",
                temperature=0.2
            )
        return None

    def invoke(self, messages: List[BaseMessage], force_local: bool = False) -> BaseMessage:
        sanitized_messages = []
        for msg in messages:
            content, _ = SecretRedactor.redact(msg.content if isinstance(msg.content, str) else str(msg.content))
            if isinstance(msg, SystemMessage):
                sanitized_messages.append(SystemMessage(content=content))
            elif isinstance(msg, HumanMessage):
                sanitized_messages.append(HumanMessage(content=content))
            else:
                sanitized_messages.append(AIMessage(content=content))

        usage_stats = self.budget_mgr.get_today_usage()
        quota_exceeded = usage_stats["is_quota_exceeded"]

        system_text = "\n\n".join(m.content for m in sanitized_messages if isinstance(m, SystemMessage))
        user_text = "\n\n".join(m.content for m in sanitized_messages if not isinstance(m, SystemMessage))

        def _log_call(provider: str, model: str, started: float, response=None, error=None, p_toks=0, c_toks=0):
            log_event(
                self.task_id, "llm_call",
                provider=provider, model=model, ok=error is None,
                duration_ms=int((time.time() - started) * 1000),
                input_tokens=p_toks, output_tokens=c_toks,
                system_prompt=preview(system_text, 1500), prompt=preview(user_text, 6000),
                response=preview(response.content, 8000) if response is not None else None,
                error=str(error) if error else None,
            )

        # 1. Attempt Cloud Execution down the provider chain
        if quota_exceeded:
            log_event(self.task_id, "quota_exceeded", usage=usage_stats)
        if not quota_exceeded and not force_local:
            for name, model, llm in self.cloud_chain:
                started = time.time()
                try:
                    response = llm.invoke(sanitized_messages)
                    usage = getattr(response, "usage_metadata", {}) or {}
                    p_toks = usage.get("input_tokens", 0)
                    c_toks = usage.get("output_tokens", 0)
                    _log_call(name, model, started, response=response, p_toks=p_toks, c_toks=c_toks)
                    if p_toks or c_toks:
                        self.budget_mgr.record_usage(
                            task_id=self.task_id,
                            provider=f"{name}_cloud",
                            model=model,
                            prompt_tokens=p_toks,
                            completion_tokens=c_toks
                        )
                    return response
                except Exception as e:
                    _log_call(name, model, started, error=e)
                    print(f"⚠️ [HybridRouter] {name} error ({e}). Trying next provider...")

        # 2. Fallback to Local Ollama
        if self.local_llm:
            started = time.time()
            try:
                response = self.local_llm.invoke(sanitized_messages)
            except Exception as e:
                _log_call("ollama", config.local_model, started, error=e)
                return AIMessage(content=f"[Error: No valid Cloud or Local LLM provider reachable ({e})]")
            _log_call("ollama", config.local_model, started, response=response,
                      p_toks=len(str(sanitized_messages)) // 4, c_toks=len(str(response.content)) // 4)
            self.budget_mgr.record_usage(
                task_id=self.task_id,
                provider="ollama_local",
                model=config.local_model,
                prompt_tokens=len(str(sanitized_messages)) // 4,
                completion_tokens=len(str(response.content)) // 4
            )
            return response

        return AIMessage(content="[Error: No valid Cloud or Local LLM provider reachable]")
