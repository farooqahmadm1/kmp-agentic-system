import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class TokenBudgetManager:
    """Tracks token usage across tasks in SQLite to enforce quotas and cost caps."""

    def __init__(self, db_path: str = ".sessions/token_budget.db", daily_token_limit: int = 100_000):
        self.daily_limit = daily_token_limit
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
        # Estimate cost ($1.40 / 1M input, $2.80 / 1M output for DeepSeek Chat)
        if "deepseek" in provider.lower():
            cost = (prompt_tokens * 0.0000014) + (completion_tokens * 0.0000028)
        else:
            cost = 0.0 # Local Ollama is free

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
                    COALESCE(SUM(CASE WHEN provider LIKE '%deepseek%' THEN total_tokens ELSE 0 END), 0)
                FROM token_ledger 
                WHERE DATE(timestamp) = DATE('now')
            """)
            row = cursor.fetchone()
            return {
                "total_tokens_today": row[0],
                "total_cost_usd_today": row[1],
                "cloud_tokens_today": row[2],
                "daily_limit": self.daily_limit,
                "is_quota_exceeded": row[2] >= self.daily_limit
            }
