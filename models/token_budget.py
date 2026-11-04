import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

class TokenBudgetManager:
    """Tracks token usage across tasks in SQLite to enforce quotas and cost caps."""

    # USD per 1M (input, output) tokens, matched by provider-name prefix; override via `models.pricing_usd_per_million`
    DEFAULT_PRICING: Dict[str, Tuple[float, float]] = {"deepseek": (1.40, 2.80)}

    def __init__(self, db_path: str = ".sessions/token_budget.db", daily_token_limit: int = 100_000,
                 pricing: Optional[Dict[str, Tuple[float, float]]] = None):
        self.daily_limit = daily_token_limit
        self.pricing = {k.lower(): tuple(v) for k, v in (pricing if pricing is not None else self.DEFAULT_PRICING).items()}
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS token_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    task_id TEXT,
                    provider TEXT,
                    model TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    estimated_cost_usd REAL
                )
            """)
            conn.commit()

    def record_usage(self, task_id: str, provider: str, model: str, prompt_tokens: int, completion_tokens: int):
        total = prompt_tokens + completion_tokens
        # Subscription CLIs, local Ollama and unpriced providers count as $0 (their tokens still count toward the quota)
        cost = 0.0
        for prefix, (in_price, out_price) in self.pricing.items():
            if provider.lower().startswith(prefix):
                cost = (prompt_tokens * in_price + completion_tokens * out_price) / 1_000_000
                break

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO token_ledger 
                   (task_id, provider, model, prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (task_id, provider, model, prompt_tokens, completion_tokens, total, cost)
            )
            conn.commit()

    def get_today_usage(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(total_tokens), 0),
                    COALESCE(SUM(estimated_cost_usd), 0.0),
                    COALESCE(SUM(CASE WHEN provider NOT LIKE '%local' THEN total_tokens ELSE 0 END), 0)
                FROM token_ledger 
                WHERE DATE(timestamp) = DATE('now')
            """)
            row = cursor.fetchone()
            return {
                "total_tokens_today": row[0],
                "total_cost_usd_today": row[1],
                "cloud_tokens_today": row[2],
                "daily_limit": self.daily_limit,
                # Every cloud provider (API key or subscription CLI) counts; only local models are exempt
                "is_quota_exceeded": row[2] >= self.daily_limit
            }
