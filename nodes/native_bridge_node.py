from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from state import KMPGraphState, KMPFileSpec
from models.hybrid_router import HybridModelRouter
from models.prompt_templates import NATIVE_BRIDGE_SYSTEM_PROMPT
from skills.skill_registry import KMPSkillRegistry

def native_bridge_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 4: Native Bridge Specialist generates expect/actual declarations across platforms."""
    plan = state.get("plan")
    task_id = state.get("task_id", "default")
    if not plan or not plan.bridges:
        return {"files": {}}

    skill_registry = KMPSkillRegistry()
    skill_context = skill_registry.get_skills_for_node("native_bridge_node")
    router = HybridModelRouter(task_id=task_id)

    generated_files: Dict[str, KMPFileSpec] = {}
    for bridge in plan.bridges:
        # 1. Expect declaration
        exp = bridge.expect_declaration
        generated_files[exp.file_path] = exp
        
        # 2. Actual implementations
        for plat, act in bridge.actual_implementations.items():
            prompt = f"Implement Kotlin 2.x 'actual' for {bridge.interface_name} on {plat}.\nPath: {act.file_path}\n\n{skill_context}"
            res = router.invoke([
                SystemMessage(content=NATIVE_BRIDGE_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            clean_code = res.content
            if "```kotlin" in clean_code:
                clean_code = clean_code.split("```kotlin")[1].split("```")[0].strip()
            elif "```" in clean_code:
                clean_code = clean_code.split("```")[1].split("```")[0].strip()

            generated_files[act.file_path] = KMPFileSpec(
                file_path=act.file_path,
                source_set=act.source_set,
                content=clean_code if clean_code else act.content,
                description=act.description
            )

    return {
        "files": generated_files,
        "messages": [AIMessage(content=f"Native Bridge Agent implemented {len(plan.bridges)} expect/actual bridge sets.")]
    }
