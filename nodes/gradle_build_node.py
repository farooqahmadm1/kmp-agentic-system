from typing import Dict, Any
from langchain_core.messages import AIMessage
from state import KMPGraphState
from config import config
from tools.gradle_runner import GradleBuildRunner
from memory.episodic_store import EpisodicMemoryStore

def gradle_build_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 8: Executes isolated Gradle tasks and captures compilation diagnostics."""
    workspace_root = state.get("workspace_root", ".")
    project = config.get_project(state.get("project_name", ""))
    runner = GradleBuildRunner(workspace_root, allow_simulated=config.allow_simulated_build and not project)
    result = runner.run_task(*project.get("gradle_tasks", ["check"]))

    status = "success" if result["success"] else "failed"
    diagnostics = result.get("diagnostics", [])

    if status == "success" and not result.get("simulated"):
        _learn_fix(state)

    note = " (SIMULATED - nothing was compiled)" if result.get("simulated") else ""
    return {
        "build_status": status,
        "build_simulated": bool(result.get("simulated")),
        "build_fatal": bool(result.get("fatal")),
        "build_output_tail": result.get("output_tail", ""),
        "compiler_diagnostics": diagnostics,
        "messages": [AIMessage(content=f"Gradle Build Execution: Status={status.upper()}{note} ({len(diagnostics)} diagnostics captured).")]
    }

def _learn_fix(state: KMPGraphState):
    """After a build that a fix iteration repaired, store the error -> fix recipe in episodic memory."""
    previous = state.get("compiler_diagnostics") or []
    fix_notes = state.get("fix_notes") or ""
    if state.get("iteration_count", 0) == 0 or not previous or not fix_notes:
        return
    if fix_notes.startswith("The security guardrail"):  # last retry fixed a guardrail issue, not this error
        return
    first = previous[0]
    signature = first.error_message.strip()[:200]
    if len(signature) < 12:  # too generic to match future errors usefully
        return
    try:
        EpisodicMemoryStore().record_solution(
            error_signature=signature,
            category=first.responsible_agent,
            root_cause=f"{first.file_path}:{first.line}",
            recipe=fix_notes[:2000],
        )
    except Exception:
        pass  # learning is best-effort and must never fail a build
