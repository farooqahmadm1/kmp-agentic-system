"""Local web dashboard: start agent runs, approve their plan/diff gates, and browse live
progress and full history.

    python cli.py web            # http://127.0.0.1:8765

Runs started here execute in background threads of this server process, and their HITL gates
wait for the Approve/Reject buttons. Runs started from the CLI are shown too, but their gates
are answered in that terminal. History comes from the per-task JSONL trajectory logs
(memory/trajectory_log.py), the session table and the token ledger. Standard library only.

Only binds to localhost and has no authentication — do not expose it to a network as-is.
"""
import json
import sqlite3
import threading
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from config import config
from memory.trajectory_log import list_task_ids, read_events

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "[::1]"}

STATIC_DIR = Path(__file__).resolve().parent / "web"
STALE_AFTER_SECONDS = 45 * 60  # a run with no events for this long probably died


class WebRuns:
    """Background task threads started from the dashboard, and their pending approval gates."""

    def __init__(self):
        self._lock = threading.Lock()
        self.threads = {}   # task_id -> Thread
        self.pending = {}   # task_id -> {"gate": str, "event": Event, "approved": bool}

    def start(self, description: str, project: str, platforms) -> str:
        from task_runner import new_task_id, run_task
        tid = new_task_id()

        def approve(gate: str, info: dict) -> bool:
            slot = {"gate": gate, "event": threading.Event(), "approved": False}
            with self._lock:
                self.pending[tid] = slot
            slot["event"].wait()
            with self._lock:
                self.pending.pop(tid, None)
            return slot["approved"]

        def target():
            try:
                run_task(tid, description, project, platforms, approve, source="web", out=lambda *_: None)
            except Exception:
                traceback.print_exc()  # already logged as task_finished/ERROR by run_task
            finally:
                with self._lock:
                    self.threads.pop(tid, None)

        thread = threading.Thread(target=target, name=f"kmp-task-{tid}", daemon=True)
        with self._lock:
            self.threads[tid] = thread
        thread.start()
        return tid

    def decide(self, tid: str, gate: str, approved: bool) -> bool:
        with self._lock:
            slot = self.pending.get(tid)
            if not slot or slot["gate"] != gate:
                return False
            slot["approved"] = approved
            slot["event"].set()
            return True

    def waiting_gate(self, tid: str):
        with self._lock:
            slot = self.pending.get(tid)
            return slot["gate"] if slot else None

    def is_running(self, tid: str) -> bool:
        with self._lock:
            return tid in self.threads


RUNS = WebRuns()


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _session_rows() -> dict:
    db = config.sessions_dir / "checkpoints.db"
    if not db.exists():
        return {}
    try:
        with sqlite3.connect(db) as conn:
            conn.row_factory = sqlite3.Row
            return {r["task_id"]: dict(r) for r in conn.execute("SELECT * FROM session_metadata")}
    except sqlite3.Error:
        return {}


def summarize_task(task_id: str, events: list, session: dict) -> dict:
    started = next((e for e in events if e["type"] == "task_started"), {})
    finished = next((e for e in reversed(events) if e["type"] == "task_finished"), None)
    llm = [e for e in events if e["type"] == "llm_call"]
    builds = [e for e in events if e["type"] == "node_finished" and e.get("node") == "gradle_build_node"]
    last = events[-1] if events else {}

    if finished:
        status = finished.get("status", "COMPLETED")
    elif last.get("type") == "gate_waiting":
        status = "WAITING"
    elif events and started.get("source") == "web" and not RUNS.is_running(task_id):
        status = "STALE"  # dashboard was restarted while this run was in flight
    elif last and (datetime.now(timezone.utc) - _parse_ts(last["ts"])).total_seconds() > STALE_AFTER_SECONDS:
        status = "STALE"
    elif events:
        status = "RUNNING"
    else:
        status = session.get("status", "UNKNOWN")

    running_node = None
    if status == "RUNNING":
        open_nodes = {}
        for e in events:
            if e["type"] == "node_started":
                open_nodes[e["node"]] = e
            elif e["type"] == "node_finished":
                open_nodes.pop(e.get("node"), None)
        running_node = next(iter(open_nodes), None)

    first_ts = events[0]["ts"] if events else session.get("created_at")
    last_ts = (finished or last).get("ts") if events else session.get("updated_at")
    duration = None
    if events:
        end = datetime.now(timezone.utc) if status in ("RUNNING", "WAITING") else _parse_ts(last_ts)
        duration = (end - _parse_ts(first_ts)).total_seconds()

    return {
        "task_id": task_id,
        "description": started.get("description") or session.get("task_description", ""),
        "project": started.get("project", ""),
        "status": status,
        "running_node": running_node,
        "waiting_gate": last.get("gate") if status == "WAITING" else None,
        "started_at": first_ts,
        "updated_at": last_ts,
        "duration_s": duration,
        "llm_calls": len(llm),
        "llm_failures": sum(1 for e in llm if not e.get("ok")),
        "tokens": sum((e.get("input_tokens") or 0) + (e.get("output_tokens") or 0) for e in llm),
        "build_attempts": len(builds),
        "build_status": builds[-1].get("build_status") if builds else None,
        "branch": session.get("branch_name") or f"agent/{task_id}",
        "source": started.get("source", "cli"),
        "can_approve": RUNS.waiting_gate(task_id) is not None,
    }


def list_tasks() -> list:
    sessions = _session_rows()
    ids = list_task_ids()
    ids += [t for t in sessions if t not in ids]
    tasks = [summarize_task(t, read_events(t), sessions.get(t, {})) for t in ids]
    return sorted(tasks, key=lambda t: t.get("started_at") or "", reverse=True)


def _provider_label(name: str) -> str:
    keys = {"anthropic": config.anthropic_api_key, "gemini": config.gemini_api_key, "deepseek": config.deepseek_api_key}
    return f"{name} (no key)" if name in keys and not keys[name] else name


def overview() -> dict:
    usage = {"today_tokens": 0, "by_provider": []}
    db = config.sessions_dir / "token_budget.db"
    if db.exists():
        try:
            with sqlite3.connect(db) as conn:
                rows = conn.execute(
                    "SELECT provider, model, COUNT(*), SUM(total_tokens) FROM token_ledger "
                    "WHERE DATE(timestamp) = DATE('now') GROUP BY provider, model"
                ).fetchall()
            usage["by_provider"] = [{"provider": p, "model": m, "calls": c, "tokens": t or 0} for p, m, c, t in rows]
            usage["today_tokens"] = sum(r["tokens"] for r in usage["by_provider"])
        except sqlite3.Error:
            pass
    return {
        "provider_chain": [_provider_label(p) for p in [config.cloud_provider, *config.fallback_providers, "ollama"]],
        "daily_token_limit": config.daily_token_limit,
        "projects": {name: {"path": p.get("path"), "target_platforms": p.get("target_platforms")}
                     for name, p in config.projects.items()},
        "default_project": config.default_project,
        "max_self_healing_iterations": config.max_self_healing_iterations,
        "hitl": {"plan_approval": config.hitl_plan_approval, "diff_review": config.hitl_diff_review},
        "usage": usage,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the terminal quiet
        pass

    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status: int = 200):
        self._send(status, json.dumps(data, default=str).encode("utf-8"), "application/json")

    def _host_ok(self) -> bool:
        # Guards against DNS-rebinding: only answer requests addressed to localhost
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        return host in ALLOWED_HOSTS

    def do_POST(self):
        if not self._host_ok():
            self._json({"error": "forbidden host"}, 403)
            return
        # A custom header can't be sent cross-site without a CORS preflight (which we never
        # approve), so this blocks other web pages from starting runs or approving gates.
        if self.headers.get("X-KMP-Dashboard") != "1":
            self._json({"error": "missing X-KMP-Dashboard header"}, 403)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except (ValueError, json.JSONDecodeError):
            self._json({"error": "invalid JSON"}, 400)
            return

        path = urlparse(self.path).path
        try:
            if path == "/api/tasks":
                description = (body.get("description") or "").strip()
                if not description:
                    self._json({"error": "description is required"}, 400)
                    return
                project = body.get("project") or config.default_project
                config.get_project(project)  # validates the name (KeyError -> 400)
                platforms = [p for p in (body.get("platforms") or []) if p in ("android", "ios", "desktop", "wasmJs")] or None
                tid = RUNS.start(description, project, platforms)
                self._json({"task_id": tid}, 201)
            elif path.startswith("/api/tasks/") and path.endswith("/gate"):
                tid = unquote(path[len("/api/tasks/"):-len("/gate")])
                ok = RUNS.decide(tid, body.get("gate", ""), bool(body.get("approved")))
                if ok:
                    self._json({"ok": True})
                else:
                    self._json({"error": "this run is not waiting for that approval here"}, 409)
            else:
                self._json({"error": "not found"}, 404)
        except KeyError as e:
            self._json({"error": str(e).strip("'\"")}, 400)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def do_GET(self):
        if not self._host_ok():
            self._json({"error": "forbidden host"}, 403)
            return
        path = urlparse(self.path).path
        try:
            if path in ("/", "/index.html"):
                self._send(200, (STATIC_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif path == "/api/overview":
                self._json(overview())
            elif path == "/api/tasks":
                self._json(list_tasks())
            elif path.startswith("/api/tasks/"):
                task_id = unquote(path[len("/api/tasks/"):])
                events = read_events(task_id)
                session = _session_rows().get(task_id, {})
                if not events and not session:
                    self._json({"error": "not found"}, 404)
                    return
                self._json({"summary": summarize_task(task_id, events, session), "events": events})
            else:
                self._json({"error": "not found"}, 404)
        except Exception as e:
            self._json({"error": str(e)}, 500)


def serve(host: str = "127.0.0.1", port: int = 8765):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"KMP agent dashboard: http://{host}:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
