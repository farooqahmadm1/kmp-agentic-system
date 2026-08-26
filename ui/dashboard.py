import asyncio
from typing import Dict, Any, List
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

class KMPDashboard:
    """Rich Terminal Observability Dashboard for KMP Agentic System."""

    def __init__(self, task_id: str, branch_name: str, daily_token_limit: int = 100_000):
        self.console = Console()
        self.task_id = task_id
        self.branch_name = branch_name
        self.daily_token_limit = daily_token_limit
        
        # State metrics
        self.used_tokens = 0
        self.cloud_cost = 0.0
        self.episodic_hits = 0
        self.active_provider = "DeepSeek Cloud"
        
        # Trajectory steps
        self.steps: List[Dict[str, str]] = [
            {"name": "1. Init Worktree", "status": "PENDING"},
            {"name": "2. Lead Architect Node", "status": "PENDING"},
            {"name": "3. HITL Plan Gate", "status": "PENDING"},
            {"name": "4. Core Domain Node", "status": "PENDING"},
            {"name": "5. Compose UI Node", "status": "PENDING"},
            {"name": "6. Native Bridge Node", "status": "PENDING"},
            {"name": "7. OWASP Guardrail Gate", "status": "PENDING"},
            {"name": "8. Gradle Verification", "status": "PENDING"},
            {"name": "9. Headless UI Preview", "status": "PENDING"},
            {"name": "10. Finalize & Merge", "status": "PENDING"},
        ]
        
        # KMP Target Matrix
        self.targets: Dict[str, str] = {
            "commonMain": "PENDING",
            "androidMain": "PENDING",
            "iosMain": "PENDING",
            "desktopMain": "PENDING",
            "wasmJsMain": "PENDING"
        }
        
        # Live log buffer
        self.logs: List[str] = []

    def log(self, message: str):
        self.logs.append(message)
        if len(self.logs) > 6:
            self.logs.pop(0)

    def update_step(self, step_index: int, status: str):
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = status

    def update_tokens(self, prompt_tokens: int, completion_tokens: int, is_cloud: bool = True):
        total = prompt_tokens + completion_tokens
        if is_cloud:
            self.used_tokens += total
            self.cloud_cost += (prompt_tokens * 0.0000014) + (completion_tokens * 0.0000028)
            self.active_provider = "DeepSeek Cloud"
        else:
            self.active_provider = "Local Ollama"

    def _render_header(self) -> Panel:
        title = Text(f"🚀 KMP AGENTIC SYSTEM │ Task: {self.task_id} │ Branch: {self.branch_name} │ Provider: {self.active_provider}", style="bold cyan")
        return Panel(title, style="bold blue")

    def _render_trajectory(self) -> Panel:
        table = Table(box=None, expand=True)
        table.add_column("Pipeline Step", style="white")
        table.add_column("Status", justify="right")

        for step in self.steps:
            st = step["status"]
            if st == "DONE":
                status_text = Text("[✓] COMPLETED", style="bold green")
            elif st == "RUNNING":
                status_text = Text("[⟳] RUNNING", style="bold yellow")
            elif st == "FAILED":
                status_text = Text("[✗] FAILED", style="bold red")
            else:
                status_text = Text("[ ] QUEUED", style="dim")
            table.add_row(step["name"], status_text)

        return Panel(table, title="🤖 Agent Trajectory & State Machine", border_style="cyan")

    def _render_telemetry(self) -> Panel:
        pct = min(100, int((self.used_tokens / self.daily_token_limit) * 100)) if self.daily_token_limit > 0 else 0
        progress_bar = f"[{'█' * (pct // 5)}{'░' * (20 - (pct // 5))}] {self.used_tokens:,}/{self.daily_token_limit:,} toks ({pct}%)"
        
        telemetry_text = Text()
        telemetry_text.append("DeepSeek Cloud Token Quota:\n", style="bold")
        telemetry_text.append(f"{progress_bar}\n", style="yellow" if pct < 80 else "bold red")
        telemetry_text.append(f"Estimated Cloud Cost: ${self.cloud_cost:.4f} USD\n\n", style="green")
        telemetry_text.append("Local Ollama Engine:\n", style="bold")
        telemetry_text.append(f"Model: qwen2.5-coder:14b\n", style="white")
        telemetry_text.append(f"Episodic Cache Hits: {self.episodic_hits} (Saved ~{self.episodic_hits * 8}k toks)", style="magenta")

        return Panel(telemetry_text, title="📊 Hybrid Token & Cost Telemetry", border_style="green")

    def _render_targets(self) -> Panel:
        table = Table(expand=True)
        table.add_column("Target Source Set", style="bold")
        table.add_column("Build Status", justify="center")

        for target, st in self.targets.items():
            if st == "COMPILED":
                status_text = Text("✓ COMPILED", style="bold green")
            elif st == "BUILDING":
                status_text = Text("⟳ COMPILING", style="bold yellow")
            elif st == "ERROR":
                status_text = Text("✗ FAILED", style="bold red")
            else:
                status_text = Text("QUEUED", style="dim")
            table.add_row(target, status_text)

        return Panel(table, title="🛠️ KMP Target Matrix Build Monitor", border_style="blue")

    def _render_logs(self) -> Panel:
        log_text = Text("\n".join(self.logs) if self.logs else "Awaiting agent events...")
        return Panel(log_text, title="📝 Live Activity & Tool Stream", border_style="yellow")

    def _render_footer(self) -> Panel:
        controls = Text("[p] Pause/Resume  │  [a] Approve Plan  │  [d] Inspect Diff  │  [t] Force Local  │  [q] Quit", style="bold white on blue", justify="center")
        return Panel(controls, style="blue")

    def generate_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        layout["left"].split_column(
            Layout(name="trajectory", ratio=1),
            Layout(name="targets", ratio=1)
        )
        layout["right"].split_column(
            Layout(name="telemetry", ratio=1),
            Layout(name="logs", ratio=1)
        )

        layout["header"].update(self._render_header())
        layout["trajectory"].update(self._render_trajectory())
        layout["telemetry"].update(self._render_telemetry())
        layout["targets"].update(self._render_targets())
        layout["logs"].update(self._render_logs())
        layout["footer"].update(self._render_footer())

        return layout
