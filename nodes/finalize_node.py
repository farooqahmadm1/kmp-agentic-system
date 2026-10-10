from typing import Dict, Any
from langchain_core.messages import AIMessage
from state import KMPGraphState
from config import config
from tools.worktree_manager import KMPWorktreeManager
from memory.session_manager import SessionManager

def finalize_node(state: KMPGraphState) -> Dict[str, Any]:
    """Commits the agents' changes and generates the WALKTHROUGH.md artifact.

    For a target project the work is left on the `agent/<task-id>` branch for review;
    only the self-hosted mode (no project) merges automatically.
    """
    task_id = state.get("task_id", "default")
    plan = state.get("plan")
    project = config.get_project(state.get("project_name", ""))
    build_status = state.get("build_status", "pending")
    branch = f"agent/{task_id}"
    wt_manager = KMPWorktreeManager(project)

    # 1. Commit and get diff
    status_note = "" if build_status == "success" else " (build NOT passing)"
    wt_manager.commit_task_progress(task_id, f"feat(agent): {plan.feature_name if plan else task_id}{status_note}")
    diff = wt_manager.get_unified_diff(task_id)

    # 2. Hand off: keep branch for review (project) or merge (self-hosted)
    if project:
        wt_manager.remove_worktree(task_id)
        outcome = f"Changes are on branch '{branch}' in {project['path']} — review and merge it yourself."
    else:
        merged = wt_manager.merge_and_prune(task_id)
        outcome = "Worktree merged." if merged else f"Merge failed; changes remain on '{branch}'."

    # 3. Update session metadata in SQLite
    session_mgr = SessionManager()
    session_mgr.update_session_status(task_id, "COMPLETED" if build_status == "success" else "FAILED")
    bundle_dir = session_mgr.export_session_bundle(task_id)
    (bundle_dir / "changes.diff").write_text(diff, encoding="utf-8")

    # 4. Write WALKTHROUGH.md artifact
    walkthrough_content = f"""# Walkthrough: {plan.feature_name if plan else task_id}

## Summary
{outcome}

## Architecture Overview
{plan.architecture_overview if plan else 'N/A'}

## Generated Files
{chr(10).join('- ' + f for f in state.get('files', {}).keys())}

## Build Verification
- Gradle Status: {build_status.upper()}
- Iterations: {state.get('iteration_count', 0)}
"""
    (bundle_dir / "WALKTHROUGH.md").write_text(walkthrough_content, encoding="utf-8")

    return {
        "messages": [AIMessage(content=f"Task '{task_id}' finalized. {outcome} Walkthrough: {bundle_dir / 'WALKTHROUGH.md'}")]
    }
