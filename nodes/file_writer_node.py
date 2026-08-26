from typing import Dict, Any
from langchain_core.messages import AIMessage
from state import KMPGraphState
from tools.kmp_workspace import KMPWorkspaceManager

def file_writer_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 7: Writes validated files directly to the task's isolated Git Worktree."""
    workspace_root = state.get("workspace_root", ".")
    files = state.get("files", {})
    ws_manager = KMPWorkspaceManager(workspace_root)

    written_count = 0
    for path, spec in files.items():
        ws_manager.write_file(spec)
        written_count += 1

    return {
        "messages": [AIMessage(content=f"Sandboxed File Writer committed {written_count} files to worktree.")]
    }
