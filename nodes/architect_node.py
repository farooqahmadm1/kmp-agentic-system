import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from state import KMPGraphState, KMPPlan, KMPFileSpec, ExpectActualBridge
from models.hybrid_router import HybridModelRouter
from models.prompt_templates import ARCHITECT_SYSTEM_PROMPT
from models.json_repair import JSONRepair
from memory.graphify_store import GraphifyASTStore
from skills.skill_registry import KMPSkillRegistry
from nodes.project_context import project_overview

def architect_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 1: Lead Architect decomposes feature request into typed KMPPlan."""
    task_id = state.get("task_id", "default")
    description = state.get("task_description", "")
    workspace_root = state.get("workspace_root", ".")

    # 1. Query Graphify AST context
    graphify = GraphifyASTStore(workspace_root)
    graphify.scan_and_index()
    ast_context = graphify.get_context_subgraph(["App", "MainViewModel", "UserRepository"])

    # 2. Retrieve progressive skills
    skill_registry = KMPSkillRegistry()
    skill_context = skill_registry.get_skills_for_node("gradle_build_node")

    # 3. Call Hybrid Router
    platforms = state.get("target_platforms") or ["android", "ios", "desktop", "wasmJs"]
    overview = project_overview(workspace_root, platforms)
    project_rules = ""
    if overview:
        project_rules = (
            f"{overview}\n\n"
            "Plan this feature INTO the existing project above: use its existing packages and directories, "
            "reuse existing models/view-models, and to change an existing file list it with its exact path "
            "(its current content will be given to the coder). Use file paths relative to the KMP root as shown. "
            f"Only use source sets for: commonMain, commonTest, {', '.join(p + 'Main' for p in platforms)}."
        )
    router = HybridModelRouter(task_id=task_id)
    user_prompt = f"Feature Request: {description}\n\n{project_rules}\n\n{ast_context}\n\n{skill_context}"
    
    messages = [
        SystemMessage(content=ARCHITECT_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ]
    
    res = router.invoke(messages)
    
    # 4. Parse structured JSON output
    try:
        data = JSONRepair.parse_or_repair(res.content)
        plan = KMPPlan(
            feature_name=data.get("feature_name", "kmp_feature"),
            architecture_overview=data.get("architecture_overview", "KMP Clean Architecture"),
            target_platforms=data.get("target_platforms", platforms),
            dependencies=data.get("dependencies", []),
            shared_contracts=[KMPFileSpec(**f) for f in data.get("shared_contracts", [])],
            bridges=[ExpectActualBridge(**b) for b in data.get("bridges", [])],
            ui_screens=[KMPFileSpec(**f) for f in data.get("ui_screens", [])]
        )
    except Exception as e:
        # Unparseable plan: produce an empty plan rather than writing placeholder files into the project
        plan = KMPPlan(
            feature_name="kmp_feature",
            architecture_overview=f"Architect output could not be parsed ({e}); no files generated.",
            target_platforms=platforms
        )

    return {
        "plan": plan,
        "messages": [AIMessage(content=f"Architect generated plan for feature '{plan.feature_name}' with {len(plan.shared_contracts)} shared contracts and {len(plan.bridges)} bridges.")]
    }
