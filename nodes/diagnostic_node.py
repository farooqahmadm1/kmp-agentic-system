from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from state import KMPGraphState
from models.hybrid_router import HybridModelRouter
from models.prompt_templates import DIAGNOSTIC_QA_SYSTEM_PROMPT
from memory.episodic_store import EpisodicMemoryStore
from skills.skill_registry import KMPSkillRegistry

def diagnostic_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 5: Diagnostic QA analyzes compiler errors, checks episodic memory, and produces fix recipes."""
    task_id = state.get("task_id", "default")
    diagnostics = state.get("compiler_diagnostics", [])
    output_tail = state.get("build_output_tail", "")
    iteration = state.get("iteration_count", 0) + 1

    episodic = EpisodicMemoryStore()
    skill_registry = KMPSkillRegistry()
    skill_context = skill_registry.get_skills_for_node("diagnostic_node")

    # Check episodic memory for known fixes
    matched_recipe = episodic.find_matching_fix(output_tail)

    router = HybridModelRouter(task_id=task_id)
    prompt = f"Compiler Errors:\n{output_tail}\n\nDiagnosed AST issues: {diagnostics}\n"
    if matched_recipe:
        prompt += f"\nMatched Episodic Recipe: {matched_recipe['resolution_recipe']}\n"
    prompt += f"\n{skill_context}"

    res = router.invoke([
        SystemMessage(content=DIAGNOSTIC_QA_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    return {
        "iteration_count": iteration,
        "messages": [AIMessage(content=f"Diagnostic QA Agent evaluated errors (Iteration {iteration}). Applied fix strategy: {res.content[:200]}...")]
    }
