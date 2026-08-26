from typing import Dict, Any
from pathlib import Path
from langchain_core.messages import AIMessage
from state import KMPGraphState
from tools.worktree_manager import KMPWorktreeManager
from memory.session_manager import SessionManager

def finalize_node(state: KMPGraphState) -> Dict[str, Any]:
    """Commits passing changes, merges the worktree branch, and generates the WALKTHROUGH.md artifact."""
    task_id = state.get("task_id", "default")
    plan = state.get("plan")
    workspace_root = state.get("workspace_root", ".")
    wt_manager = KMPWorktreeManager()
    
    # 1. Commit and get diff
    wt_manager.commit_task_progress(task_id, f"feat: completed {task_id}")
    diff = wt_manager.get_unified_diff(task_id)

    # 2. Merge worktree branch into main
    wt_manager.merge_and_prune(task_id)

    # 3. Update session metadata in SQLite
    session_mgr = SessionManager()
    session_mgr.update_session_status(task_id, "COMPLETED")
    bundle_dir = session_mgr.export_session_bundle(task_id)

    # 4. Write WALKTHROUGH.md artifact
    walkthrough_content = f"""# Walkthrough: {plan.feature_name if plan else task_id}

## Summary
Successfully implemented feature across target platforms.

## Architecture Overview
{plan.architecture_overview if plan else 'N/A'}

## Generated Files
{list(state.get('files', {}).keys())}

## Build Verification
- Gradle Status: {state.get('build_status', 'SUCCESS').upper()}
- Iterations: {state.get('iteration_count', 0)}
"""
    (bundle_dir / "WALKTHROUGH.md").write_text(walkthrough_content, encoding="utf-8")

    return {
        "messages": [AIMessage(content=f"Task '{task_id}' finalized successfully. Worktree merged and WALKTHROUGH.md created.")]
    }
