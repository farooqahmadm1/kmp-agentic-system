from typing import Dict, Any
from state import KMPGraphState
from config import config
from tools.worktree_manager import KMPWorktreeManager
from memory.session_manager import SessionManager

def init_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 7: Provisions isolated Git Worktree and registers session in SQLite."""
    task_id = state.get("task_id", "default-task")
    description = state.get("task_description", "")
    branch_name = f"agent/{task_id}"
    project = config.get_project(state.get("project_name", ""))

    # 1. Provision isolated worktree (inside the target project's repo when one is set)
    wt_manager = KMPWorktreeManager(project)
    project_root = wt_manager.create_worktree(task_id)

    # 2. Register session in SQLite checkpointer database
    session_mgr = SessionManager()
    session_mgr.register_session(task_id, description, branch_name)

    return {
        "workspace_root": str(project_root),
        "target_platforms": state.get("target_platforms") or project.get("target_platforms", config.target_platforms),
        "iteration_count": 0,
        "build_status": "pending",
        "files": {},
        "fix_notes": "",
        "compiler_diagnostics": []
    }
