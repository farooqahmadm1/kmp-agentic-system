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

def _confirm(question: str) -> bool:
    if HAS_RICH:
        return Confirm.ask(question, default=True)
    return input(f"{question} [Y/n] ").strip().lower() in ("", "y", "yes")

def _terminal_approve(gate: str, info: dict) -> bool:
    """HITL gates answered in the terminal."""
    if gate == "plan_approval":
        plan = info.get("plan")
        if plan:
            console.print(f"\n📐 Plan: {plan['feature_name']}\n{plan['architecture_overview']}")
            for f in plan["files"]:
                console.print(f"   • {f['path']} — {f['description']}")
        return _confirm("Approve this plan and generate code?")
    console.print(f"\n🔍 Build status: {info['build_status'].upper()} after {info['iterations']} fix iteration(s)")
    console.print(f"   Worktree: {info['worktree']}")
    for path in info["files"]:
        console.print(f"   • {path}")
    return _confirm("Commit these changes to the agent branch?")

def cmd_new_task(task_id: Optional[str], description: str, platforms: list, project_name: Optional[str]):
    """Launches a new KMP feature development task with interactive HITL gates."""
    from task_runner import run_task, new_task_id

    project = config.get_project(project_name or "")
    tid = task_id or new_task_id()
    target = f"{project['name']} ({project['path']})" if project else "this repository"
    console.print(f"🚀 Launching KMP Feature Task: {tid}\nTarget: {target}\nDescription: {description}")
    run_task(tid, description, project.get("name", ""), platforms, _terminal_approve,
             source="cli", out=console.print)

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

    # web
    web_parser = subparsers.add_parser("web", help="Launch the web dashboard (live runs + history)")
    web_parser.add_argument("--port", type=int, default=8765)

    # session
    session_parser = subparsers.add_parser("session", help="Manage sessions")
    session_sub = session_parser.add_subparsers(dest="session_command")
    session_sub.add_parser("list", help="List all sessions")

    # new-task
    task_parser = subparsers.add_parser("new-task", help="Run a new KMP feature task")
    task_parser.add_argument("description", type=str, help="Feature description prompt")
    task_parser.add_argument("--id", type=str, default=None, help="Custom Task ID")
    task_parser.add_argument("--targets", nargs="+", default=None, help="Target platforms (android ios desktop wasmJs)")
    task_parser.add_argument("--project", type=str, default=None, help="Target project from kmp_agent_config.yaml (default: default_project)")

    args = parser.parse_args()

    if args.command == "health":
        cmd_health()
    elif args.command == "init":
        cmd_init_starter(args.name, args.package)
    elif args.command == "tui":
        cmd_tui()
    elif args.command == "web":
        from ui.web_dashboard import serve
        serve(port=args.port)
    elif args.command == "session" and getattr(args, "session_command", None) == "list":
        cmd_session_list()
    elif args.command == "new-task":
        cmd_new_task(args.id, args.description, args.targets, args.project)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
