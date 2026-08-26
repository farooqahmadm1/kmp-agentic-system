from typing import List, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from config import config
from models.token_budget import TokenBudgetManager
from security.secret_redactor import SecretRedactor

class HybridModelRouter:
    """Dynamic Multi-Cloud LLM Gateway (Claude, Gemini, DeepSeek, Ollama)."""

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

        # 2. Cloud Provider Selection
        self.cloud_llm = None
        self.active_provider_name = config.cloud_provider

        try:
            if config.cloud_provider == "anthropic" and config.anthropic_api_key:
                from langchain_anthropic import ChatAnthropic
                self.cloud_llm = ChatAnthropic(
                    model_name=config.anthropic_model,
                    api_key=config.anthropic_api_key,
                    temperature=0.2
                )
            elif config.cloud_provider == "gemini" and config.gemini_api_key:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.cloud_llm = ChatGoogleGenerativeAI(
                    model=config.gemini_model,
                    google_api_key=config.gemini_api_key,
                    temperature=0.2
                )
            elif config.deepseek_api_key: # default deepseek
                from langchain_openai import ChatOpenAI
                self.cloud_llm = ChatOpenAI(
                    model=config.deepseek_model,
                    api_key=config.deepseek_api_key,
                    base_url="https://api.deepseek.com/v1",
                    temperature=0.2
                )
        except Exception as e:
            print(f"Notice: Cloud provider {config.cloud_provider} initialization: {e}")

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

        # 1. Attempt Cloud Execution (Claude / Gemini / DeepSeek)
        if self.cloud_llm and not quota_exceeded and not force_local:
            try:
                response = self.cloud_llm.invoke(sanitized_messages)
                usage = getattr(response, "usage_metadata", {}) or {}
                p_toks = usage.get("input_tokens", 0)
                c_toks = usage.get("output_tokens", 0)
                if p_toks or c_toks:
                    self.budget_mgr.record_usage(
                        task_id=self.task_id,
                        provider=f"{self.active_provider_name}_cloud",
                        model=getattr(config, f"{self.active_provider_name}_model", "cloud"),
                        prompt_tokens=p_toks,
                        completion_tokens=c_toks
                    )
                return response
            except Exception as e:
                print(f"⚠️ [HybridRouter] {self.active_provider_name} Cloud error ({e}). Switching to local Ollama...")

        # 2. Fallback to Local Ollama
        if self.local_llm:
            response = self.local_llm.invoke(sanitized_messages)
            self.budget_mgr.record_usage(
                task_id=self.task_id,
                provider="ollama_local",
                model=config.local_model,
                prompt_tokens=len(str(sanitized_messages)) // 4,
                completion_tokens=len(str(response.content)) // 4
            )
            return response

        return AIMessage(content="[Error: No valid Cloud or Local LLM provider reachable]")
