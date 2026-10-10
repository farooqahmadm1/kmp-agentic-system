from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from state import KMPGraphState, KMPFileSpec
from models.hybrid_router import HybridModelRouter
from models.prompt_templates import NATIVE_BRIDGE_SYSTEM_PROMPT
from skills.skill_registry import KMPSkillRegistry
from nodes.project_context import coder_prompt, extract_code

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
            prompt = coder_prompt(
                state, act,
                f"Implement the Kotlin 2.x 'actual' for {bridge.interface_name} on {plat}, matching this expect declaration:\n"
                f"```kotlin\n{exp.content}\n```\nFile",
                skill_context,
                generated_files
            )
            res = router.invoke([
                SystemMessage(content=NATIVE_BRIDGE_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            clean_code = extract_code(res.content)

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
