from typing import Optional
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import Header, Footer, Static, Log, Label, Button, ProgressBar
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False

from memory.session_manager import SessionManager
from models.token_budget import TokenBudgetManager
from config import config

if HAS_TEXTUAL:
    class KMPAgentTUI(App):
        """Interactive Terminal UI Application for KMP Agentic System."""
        
        CSS = """
        Screen {
            layout: vertical;
            background: #0d1117;
            color: #c9d1d9;
        }
        #top-bar {
            height: 3;
            background: #161b22;
            color: #58a6ff;
            content-align: center middle;
            text-style: bold;
        }
        #main-container {
            layout: horizontal;
            height: 1fr;
        }
        #left-pane {
            width: 30%;
            background: #161b22;
            border-right: solid #30363d;
            padding: 1;
        }
        #center-pane {
            width: 45%;
            padding: 1;
        }
        #right-pane {
            width: 25%;
            background: #161b22;
            border-left: solid #30363d;
            padding: 1;
        }
        .pane-title {
            text-style: bold;
            color: #79c0ff;
            margin-bottom: 1;
        }
        Log {
            background: #010409;
            border: solid #30363d;
            height: 1fr;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("a", "approve", "Approve Plan"),
            ("d", "diff", "View Diff"),
            ("r", "refresh", "Refresh Sessions")
        ]

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("🚀 KMP Multi-Agent Orchestrator Control Center", id="top-bar")
            with Horizontal(id="main-container"):
                with Vertical(id="left-pane"):
                    yield Label("📋 Active Sessions", classes="pane-title")
                    yield Static(id="sessions-list")
                with Vertical(id="center-pane"):
                    yield Label("📝 Live Agent Activity Stream", classes="pane-title")
                    yield Log(id="activity-log")
                with Vertical(id="right-pane"):
                    yield Label("📊 Token Budget & Targets", classes="pane-title")
                    yield Static(id="telemetry-info")
            yield Footer()

        def on_mount(self) -> None:
            self.refresh_dashboard()

        def refresh_dashboard(self) -> None:
            # Refresh sessions
            mgr = SessionManager()
            sessions = mgr.list_sessions()
            sess_text = "\n".join([f"• [{s['status']}] {s['task_id']}\n  {s['task_description'][:30]}..." for s in sessions[:5]])
            self.query_one("#sessions-list", Static).update(sess_text or "No active sessions.")

            # Refresh telemetry
            budget = TokenBudgetManager()
            usage = budget.get_today_usage()
            telemetry_text = f"Cloud Tokens Today: {usage['cloud_tokens_today']:,} / {usage['daily_limit']:,}\n" \
                             f"Estimated Cost: ${usage['total_cost_usd_today']:.4f}\n\n" \
                             f"KMP Target Matrix:\n" \
                             f"✓ commonMain\n✓ androidMain\n✓ iosMain (SKIE)\n✓ desktopMain\n✓ wasmJsMain"
            self.query_one("#telemetry-info", Static).update(telemetry_text)

            log_view = self.query_one("#activity-log", Log)
            log_view.write_line("Agentic system ready. Waiting for tasks...")

        def action_approve(self) -> None:
            log_view = self.query_one("#activity-log", Log)
            log_view.write_line("✅ [HITL Gate] Developer approved architecture plan.")

        def action_diff(self) -> None:
            log_view = self.query_one("#activity-log", Log)
            log_view.write_line("🔍 [Diff Inspector] Inspecting active worktree branch...")

        def action_refresh(self) -> None:
            self.refresh_dashboard()

def run_tui():
    if HAS_TEXTUAL:
        app = KMPAgentTUI()
        app.run()
    else:
        print("Textual is not installed. Install with: pip install textual")
