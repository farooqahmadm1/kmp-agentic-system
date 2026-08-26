import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from state import KMPGraphState, KMPPlan, KMPFileSpec, ExpectActualBridge
from models.hybrid_router import HybridModelRouter
from models.prompt_templates import ARCHITECT_SYSTEM_PROMPT
from models.json_repair import JSONRepair
from memory.graphify_store import GraphifyASTStore
from skills.skill_registry import KMPSkillRegistry

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
    router = HybridModelRouter(task_id=task_id)
    user_prompt = f"Feature Request: {description}\n\n{ast_context}\n\n{skill_context}"
    
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
            target_platforms=data.get("target_platforms", ["android", "ios", "desktop", "wasmJs"]),
            dependencies=data.get("dependencies", []),
            shared_contracts=[KMPFileSpec(**f) for f in data.get("shared_contracts", [])],
            bridges=[ExpectActualBridge(**b) for b in data.get("bridges", [])],
            ui_screens=[KMPFileSpec(**f) for f in data.get("ui_screens", [])]
        )
    except Exception as e:
        # Fallback default plan if parsing fails
        plan = KMPPlan(
            feature_name="kmp_feature",
            architecture_overview=f"Decomposed architecture for: {description}",
            shared_contracts=[
                KMPFileSpec(
                    file_path="composeApp/src/commonMain/kotlin/domain/Model.kt",
                    source_set="commonMain",
                    content="package domain\n\ndata class FeatureState(val isActive: Boolean = true)\n",
                    description="Domain state model"
                )
            ]
        )

    return {
        "plan": plan,
        "messages": [AIMessage(content=f"Architect generated plan for feature '{plan.feature_name}' with {len(plan.shared_contracts)} shared contracts and {len(plan.bridges)} bridges.")]
    }
