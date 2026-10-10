"""Append-only JSONL event log per task, read by the web dashboard (ui/web_dashboard.py).

One file per task in `.logs/trajectory/<task_id>.jsonl`; every line is one event:
{"ts": ISO-8601, "type": "...", "node": "...", ...event fields}
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import config

_lock = threading.Lock()
# Node currently executing, so events from shared helpers (e.g. LLM calls) can be attributed to it
_current_node: Dict[str, str] = {}

TRAJECTORY_DIR = config.logs_dir / "trajectory"


def _path(task_id: str) -> Path:
    safe = "".join(c for c in task_id if c.isalnum() or c in "-_.") or "default"
    return TRAJECTORY_DIR / f"{safe}.jsonl"


def set_current_node(task_id: str, node: Optional[str]):
    if node:
        _current_node[task_id] = node
    else:
        _current_node.pop(task_id, None)


def log_event(task_id: str, event_type: str, **fields: Any):
    """Appends one event; never raises (observability must not break a run)."""
    try:
        event = {"ts": datetime.now(timezone.utc).isoformat(), "type": event_type}
        if "node" not in fields and task_id in _current_node:
            event["node"] = _current_node[task_id]
        event.update(fields)
        line = json.dumps(event, default=str, ensure_ascii=False)
        TRAJECTORY_DIR.mkdir(parents=True, exist_ok=True)
        with _lock, open(_path(task_id), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def read_events(task_id: str) -> List[Dict[str, Any]]:
    path = _path(task_id)
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def list_task_ids() -> List[str]:
    if not TRAJECTORY_DIR.exists():
        return []
    files = sorted(TRAJECTORY_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.stem for p in files]


def preview(text: Any, limit: int = 4000) -> str:
    text = text if isinstance(text, str) else str(text)
    return text if len(text) <= limit else text[:limit] + f"\n… ({len(text) - limit} more chars)"
