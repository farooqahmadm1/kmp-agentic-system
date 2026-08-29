import argparse
import sys
import uuid
import os
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    class SimpleConsole:
        def print(self, *args, **kwargs):
            clean_args = [str(a).replace("[bold cyan]", "").replace("[/bold cyan]", "")
                                 .replace("[bold green]", "").replace("[/bold green]", "")
                                 .replace("[bold blue]", "").replace("[/bold blue]", "")
                                 .replace("[green]", "").replace("[/green]", "")
                                 .replace("[yellow]", "").replace("[/yellow]", "")
                                 .replace("[red]", "").replace("[/red]", "")
                                 .replace("[cyan]", "").replace("[/cyan]", "") for a in args]
            print(*clean_args)
    console = SimpleConsole()

from config import config
from tools.health_checker import HealthChecker
from memory.session_manager import SessionManager
from tools.kmp_scaffolder import KMPProjectScaffolder

def cmd_health():
    """Performs pre-flight health checks for Ollama and Cloud APIs."""
    res = HealthChecker.check_all()
    if HAS_RICH:
        table = Table(title="🔍 Pre-Flight Health Check", expand=True)
        table.add_column("Component", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Details", style="white")

        table.add_row(
            "Local Ollama",
            "[green]ONLINE[/green]" if res["ollama_active"] else "[red]OFFLINE[/red]",
            res["ollama_message"]
        )
        table.add_row(
            "Active Cloud Provider",
            f"[green]{config.cloud_provider.upper()}[/green]",
            f"Daily Quota: {res['daily_token_limit']:,} tokens"
        )
        console.print(table)
    else:
        print("================== Pre-Flight Health Check ==================")
        print(f"Local Ollama:   {'ONLINE' if res['ollama_active'] else 'OFFLINE'} - {res['ollama_message']}")
        print(f"Cloud Provider: {config.cloud_provider.upper()} - Daily Quota: {res['daily_token_limit']:,} tokens")
        print("=============================================================")

def cmd_session_list():
    """Lists all active, paused, and completed sessions."""
    mgr = SessionManager()
    sessions = mgr.list_sessions()
    if not sessions:
        console.print("[yellow]No active or past sessions found.[/yellow]")
        return

    if HAS_RICH:
        table = Table(title="📋 KMP Agent Sessions", expand=True)
        table.add_column("Task ID", style="bold cyan")
        table.add_column("Branch", style="green")
        table.add_column("Description", style="white")
        table.add_column("Status", justify="center")
        table.add_column("Last Updated", style="dim")

        for s in sessions:
            status_style = "green" if s["status"] == "COMPLETED" else "yellow"
            table.add_row(s["task_id"], s["branch_name"], s["task_description"], f"[{status_style}]{s['status']}[/{status_style}]", str(s["updated_at"]))

        console.print(table)
    else:
        print("================== KMP Agent Sessions ==================")
        for s in sessions:
            print(f"- Task ID: {s['task_id']} | Branch: {s['branch_name']} | Status: {s['status']} | Desc: {s['task_description']}")
        print("========================================================")

def cmd_new_task(task_id: Optional[str], description: str, platforms: list):
    """Launches a new KMP feature development task with interactive HITL gates."""
    from graph import create_kmp_graph
    
    tid = task_id or f"task-{uuid.uuid4().hex[:8]}"
    console.print(f"🚀 Launching KMP Feature Task: {tid}\nDescription: {description}")
    
    app = create_kmp_graph()
    app_config = {"configurable": {"thread_id": tid}}

    initial_state = {
        "messages": [],
        "task_id": tid,
        "task_description": description,
        "target_platforms": platforms or config.target_platforms,
        "workspace_root": ".",
        "iteration_count": 0,
        "max_iterations": config.max_self_healing_iterations,
        "build_status": "pending",
        "compiler_diagnostics": []
    }

    # Execute graph with stream
    for event in app.stream(initial_state, config=app_config):
        for node_name, state_update in event.items():
            console.print(f"  ✓ Completed node: {node_name}")

    console.print(f"\n🎉 Task '{tid}' execution cycle completed successfully!")

def cmd_init_starter(app_name: str, package_name: str):
    """Scaffolds a production-grade Kotlin 2.x + Compose Multiplatform starter template."""
    console.print(f"📦 Scaffolding fresh Kotlin Multiplatform project '{app_name}' ({package_name})...")
    KMPProjectScaffolder.scaffold(
        root_dir=".",
        app_name=app_name,
        package_name=package_name
    )
    console.print("✓ Scaffolding complete. Target source sets (Android, iOS, Desktop, Wasm) and version catalog generated.")

def cmd_tui():
    """Launches the interactive Textual TUI control center."""
    from ui.tui_app import run_tui
    run_tui()

def main():
    parser = argparse.ArgumentParser(description="KMP Multi-Agent System CLI")
    subparsers = parser.add_subparsers(dest="command")

    # health
    subparsers.add_parser("health", help="Run pre-flight connectivity checks")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize full starter KMP project structure")
    init_parser.add_argument("--name", type=str, default="ComposeApp", help="Application name")
    init_parser.add_argument("--package", type=str, default="com.example.kmp", help="Root package identifier")

    # tui
    subparsers.add_parser("tui", help="Launch interactive Terminal UI dashboard")

    # session
    session_parser = subparsers.add_parser("session", help="Manage sessions")
    session_sub = session_parser.add_subparsers(dest="session_command")
    session_sub.add_parser("list", help="List all sessions")

    # new-task
    task_parser = subparsers.add_parser("new-task", help="Run a new KMP feature task")
    task_parser.add_argument("description", type=str, help="Feature description prompt")
    task_parser.add_argument("--id", type=str, default=None, help="Custom Task ID")
    task_parser.add_argument("--targets", nargs="+", default=None, help="Target platforms (android ios desktop wasmJs)")

    args = parser.parse_args()

    if args.command == "health":
        cmd_health()
    elif args.command == "init":
        cmd_init_starter(args.name, args.package)
    elif args.command == "tui":
        cmd_tui()
    elif args.command == "session" and getattr(args, "session_command", None) == "list":
        cmd_session_list()
    elif args.command == "new-task":
        cmd_new_task(args.id, args.description, args.targets)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
