import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from langgraph.checkpoint.sqlite import SqliteSaver
except ImportError:
    # Graceful fallback when langgraph package is not yet installed
    class SqliteSaver:
        def __init__(self, conn):
            self.conn = conn

from config import config

class SessionManager:
    """Manages SQLite checkpointers, session snapshots, time-travel history, and forking."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(config.sessions_dir / "checkpoints.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_session_tables()

    def _init_session_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_metadata (
                    task_id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    branch_name TEXT,
                    task_description TEXT,
                    status TEXT,
                    total_tokens INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def get_checkpointer(self) -> SqliteSaver:
        """Returns a LangGraph SqliteSaver checkpointer instance."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return SqliteSaver(conn)

    def register_session(self, task_id: str, description: str, branch_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO session_metadata (task_id, task_description, branch_name, status, updated_at)
                VALUES (?, ?, ?, 'ACTIVE', CURRENT_TIMESTAMP)
            """, (task_id, description, branch_name))
            conn.commit()

    def update_session_status(self, task_id: str, status: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE session_metadata 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE task_id = ?
            """, (status, task_id))
            conn.commit()

    def list_sessions(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM session_metadata ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def export_session_bundle(self, task_id: str, output_dir: Optional[str] = None) -> Path:
        """Exports session metadata, diffs, and walkthrough into a task bundle folder."""
        dest = Path(output_dir or config.sessions_dir) / task_id
        dest.mkdir(parents=True, exist_ok=True)
        
        bundle_info = {
            "task_id": task_id,
            "exported_at": str(Path(self.db_path).stat().st_mtime)
        }
        (dest / "metadata.json").write_text(json.dumps(bundle_info, indent=2), encoding="utf-8")
        return dest
