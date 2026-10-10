"""Runs one KMP feature task through the LangGraph pipeline.

Shared by the CLI (`cli.py new-task`, approvals in the terminal) and the web dashboard
(`ui/web_dashboard.py`, approvals via buttons). The caller supplies `approve(gate, info)`,
which blocks until a human decides and returns True/False.
"""
import uuid
from typing import Callable, List, Optional

from config import config
from memory.session_manager import SessionManager
from memory.trajectory_log import log_event, preview, set_current_node

Approver = Callable[[str, dict], bool]


def new_task_id() -> str:
    return f"task-{uuid.uuid4().hex[:8]}"


def summarize_update(update) -> dict:
    """Turns a node's state update into JSON-friendly details for the trajectory log."""
    if isinstance(update, list):  # some LangGraph versions report [(channel, value), ...]
        update = dict(update)
    if not isinstance(update, dict):
        return {}
    out = {}
    msgs = update.get("messages") or []
    if msgs:
        out["summary"] = getattr(msgs[-1], "content", str(msgs[-1]))
    plan = update.get("plan")
    if plan is not None:
        out["plan"] = plan_dict(plan)
    if update.get("files"):
        out["files"] = [{"path": k, "source_set": v.source_set, "lines": v.content.count("\n") + 1,
                         "content": preview(v.content, 20000)} for k, v in update["files"].items()]
    for key in ("build_status", "iteration_count", "workspace_root", "target_platforms"):
        if key in update:
            out[key] = update[key]
    if update.get("build_output_tail"):
        out["build_output_tail"] = preview(update["build_output_tail"], 6000)
    if update.get("compiler_diagnostics"):
        out["diagnostics"] = [d.model_dump() if hasattr(d, "model_dump") else d for d in update["compiler_diagnostics"]]
    if update.get("fix_notes"):
        out["fix_notes"] = preview(update["fix_notes"], 6000)
    report = update.get("security_report")
    if report is not None:
        out["security"] = report.model_dump() if hasattr(report, "model_dump") else report
    return out


def plan_dict(plan) -> dict:
    return {
        "feature_name": plan.feature_name,
        "architecture_overview": plan.architecture_overview,
        "target_platforms": plan.target_platforms,
        "dependencies": plan.dependencies,
        "files": [{"path": f.file_path, "source_set": f.source_set, "description": f.description, "kind": kind}
                  for kind, specs in (("domain", plan.shared_contracts), ("ui", plan.ui_screens)) for f in specs]
                 + [{"path": b.expect_declaration.file_path, "source_set": "commonMain",
                     "description": f"expect {b.interface_name}", "kind": "bridge"} for b in plan.bridges],
    }


def discard_task(project: dict, tid: str):
    """Removes an abandoned task's worktree and branch (nothing was committed to it)."""
    from tools.worktree_manager import KMPWorktreeManager
    wt = KMPWorktreeManager(project)
    wt.remove_worktree(tid)
    wt._git("branch", "-D", f"agent/{tid}")
    SessionManager().update_session_status(tid, "CANCELLED")
    log_event(tid, "task_finished", status="CANCELLED")


def run_task(tid: str, description: str, project_name: str, platforms: Optional[List[str]],
             approve: Approver, source: str = "cli", out: Callable[[str], None] = print) -> str:
    """Runs the task to completion; returns the final status (COMPLETED/FAILED/CANCELLED/ERROR)."""
    from graph import create_kmp_graph
    from tools.worktree_manager import KMPWorktreeManager

    project = config.get_project(project_name or "")
    platforms = platforms or project.get("target_platforms") or config.target_platforms
    log_event(tid, "task_started", description=description, project=project.get("name", ""),
              project_path=project.get("path", ""), target_platforms=platforms, source=source,
              provider_chain=[config.cloud_provider, *config.fallback_providers, "ollama"])

    try:
        app = create_kmp_graph()
        app_config = {"configurable": {"thread_id": tid}}
        stream_input = {
            "messages": [],
            "task_id": tid,
            "task_description": description,
            "project_name": project.get("name", ""),
            "target_platforms": platforms,
            "workspace_root": ".",
            "iteration_count": 0,
            "max_iterations": config.max_self_healing_iterations,
            "build_status": "pending",
            "fix_notes": "",
            "compiler_diagnostics": []
        }

        while True:
            for event in app.stream(stream_input, config=app_config, stream_mode="debug"):
                payload = event.get("payload", {})
                node = payload.get("name")
                if event.get("type") == "task":
                    set_current_node(tid, node)
                    log_event(tid, "node_started", node=node, step=event.get("step"))
                    out(f"  … Running node: {node}")
                elif event.get("type") == "task_result":
                    err = payload.get("error")
                    log_event(tid, "node_finished", node=node, step=event.get("step"),
                              ok=not err, error=str(err) if err else None,
                              **summarize_update(payload.get("result")))
                    set_current_node(tid, None)
                    out(f"  ✓ Completed node: {node}")

            snapshot = app.get_state(app_config)
            if not snapshot.next:
                break
            values = snapshot.values

            gate, info = None, {}
            # HITL Gate 1: plan approval (graph paused before the first coder node)
            if "core_domain_node" in snapshot.next and values.get("iteration_count", 0) == 0:
                plan = values.get("plan")
                gate, info = "plan_approval", {"plan": plan_dict(plan) if plan else None}
            # HITL Gate 2: diff review before committing to the agent branch
            elif "finalize_node" in snapshot.next:
                diff = KMPWorktreeManager(project).working_diff(tid)
                gate, info = "diff_review", {
                    "build_status": values.get("build_status", "pending"),
                    "iterations": values.get("iteration_count", 0),
                    "worktree": values.get("workspace_root"),
                    "files": list(values.get("files", {})),
                    "diff": preview(diff, 60000),
                }

            if gate:
                log_event(tid, "gate_waiting", gate=gate, source=source, **info)
                approved = approve(gate, info)
                log_event(tid, "gate", gate=gate, approved=approved)
                if not approved:
                    discard_task(project, tid)
                    out(f"Task '{tid}' cancelled; worktree and branch removed.")
                    return "CANCELLED"

            stream_input = None  # resume from the checkpoint

        final = app.get_state(app_config).values
        messages = final.get("messages", [])
        status = "COMPLETED" if final.get("build_status") == "success" else "FAILED"
        summary = getattr(messages[-1], "content", "") if messages else ""
        log_event(tid, "task_finished", status=status, build_status=final.get("build_status"),
                  iterations=final.get("iteration_count", 0), branch=f"agent/{tid}", summary=summary)
        if summary:
            out(f"\n🎉 {summary}")
        return status
    except Exception as e:
        log_event(tid, "task_finished", status="ERROR", error=f"{type(e).__name__}: {e}")
        raise
    finally:
        set_current_node(tid, None)
