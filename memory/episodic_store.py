import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

class EpisodicMemoryStore:
    """Tier 4: Evolutionary Memory storing resolved Kotlin/Gradle errors and their working fixes."""

    def __init__(self, db_path: str = ".sessions/episodic_memory.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_signature TEXT UNIQUE,
                    error_category TEXT,
                    root_cause TEXT,
                    resolution_recipe TEXT,
                    hit_count INTEGER DEFAULT 1
                )
            """)
            conn.commit()

    def find_matching_fix(self, error_message: str) -> Optional[Dict[str, Any]]:
        """Queries the episodic memory for a known error signature."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Simple substring / signature search
            cursor.execute("SELECT * FROM error_recipes")
            rows = cursor.fetchall()
            for row in rows:
                sig = row["error_signature"]
                if sig.lower() in error_message.lower():
                    # Increment hit counter
                    conn.execute("UPDATE error_recipes SET hit_count = hit_count + 1 WHERE id = ?", (row["id"],))
                    conn.commit()
                    return dict(row)
        return None

    def record_solution(self, error_signature: str, category: str, root_cause: str, recipe: str):
        """Saves a newly resolved compiler error and its solution recipe to episodic memory."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO error_recipes (error_signature, error_category, root_cause, resolution_recipe)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(error_signature) DO UPDATE SET
                    resolution_recipe = excluded.resolution_recipe,
                    hit_count = hit_count + 1
            """, (error_signature, category, root_cause, recipe))
            conn.commit()
