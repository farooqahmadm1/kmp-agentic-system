from typing import Dict, Any
from langchain_core.messages import AIMessage
from state import KMPGraphState
from tools.gradle_runner import GradleBuildRunner

def gradle_build_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 8: Executes isolated Gradle tasks and captures compilation diagnostics."""
    workspace_root = state.get("workspace_root", ".")
    runner = GradleBuildRunner(workspace_root)
    result = runner.run_task("check")

    status = "success" if result["success"] else "failed"
    diagnostics = result.get("diagnostics", [])

    return {
        "build_status": status,
        "build_output_tail": result.get("output_tail", ""),
        "compiler_diagnostics": diagnostics,
        "messages": [AIMessage(content=f"Gradle Build Execution: Status={status.upper()} ({len(diagnostics)} diagnostics captured).")]
    }
