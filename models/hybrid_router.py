from typing import List, Optional
import httpx
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from config import config
from models.token_budget import TokenBudgetManager
from security.secret_redactor import SecretRedactor

class HybridModelRouter:
    """Dynamic LLM Gateway with Token Budgeting and Automatic Local Ollama Fallback."""

    def __init__(self, task_id: str = "default"):
        self.task_id = task_id
        self.budget_mgr = TokenBudgetManager(
            db_path=str(config.sessions_dir / "token_budget.db"),
            daily_token_limit=config.daily_token_limit
        )

        # 1. Local Ollama Provider (Fallback / Offline)
        self.local_llm = ChatOllama(
            base_url=config.ollama_base_url,
            model=config.local_model,
            temperature=0.2
        )

        # 2. Cloud Provider (DeepSeek Primary)
        if config.deepseek_api_key:
            self.cloud_llm = ChatOpenAI(
                model=config.cloud_model,
                api_key=config.deepseek_api_key,
                base_url="https://api.deepseek.com/v1",
                temperature=0.2
            )
        else:
            self.cloud_llm = None

    def invoke(self, messages: List[BaseMessage], force_local: bool = False) -> BaseMessage:
        # Pre-flight secret redaction on outgoing messages
        sanitized_messages = []
        for msg in messages:
            content, _ = SecretRedactor.redact(msg.content if isinstance(msg.content, str) else str(msg.content))
            if isinstance(msg, SystemMessage):
                sanitized_messages.append(SystemMessage(content=content))
            elif isinstance(msg, HumanMessage):
                sanitized_messages.append(HumanMessage(content=content))
            else:
                sanitized_messages.append(AIMessage(content=content))

        # Check quota status
        usage_stats = self.budget_mgr.get_today_usage()
        quota_exceeded = usage_stats["is_quota_exceeded"]

        # Attempt Cloud Execution if eligible
        if self.cloud_llm and not quota_exceeded and not force_local:
            try:
                response = self.cloud_llm.invoke(sanitized_messages)
                
                # Record token metrics
                usage = getattr(response, "usage_metadata", {}) or {}
                p_toks = usage.get("input_tokens", 0)
                c_toks = usage.get("output_tokens", 0)
                if p_toks or c_toks:
                    self.budget_mgr.record_usage(
                        task_id=self.task_id,
                        provider="deepseek_cloud",
                        model=config.cloud_model,
                        prompt_tokens=p_toks,
                        completion_tokens=c_toks
                    )
                return response
            except Exception as e:
                # Log error and immediately fallback to Ollama
                print(f"⚠️ [HybridRouter] Cloud provider error ({e}). Switching to local Ollama...")

        # Fallback to local Ollama
        response = self.local_llm.invoke(sanitized_messages)
        self.budget_mgr.record_usage(
            task_id=self.task_id,
            provider="ollama_local",
            model=config.local_model,
            prompt_tokens=len(str(sanitized_messages)) // 4,
            completion_tokens=len(str(response.content)) // 4
        )
        return response
