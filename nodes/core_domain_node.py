from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from state import KMPGraphState, KMPFileSpec
from models.hybrid_router import HybridModelRouter
from models.prompt_templates import CORE_DOMAIN_SYSTEM_PROMPT
from skills.skill_registry import KMPSkillRegistry
from nodes.project_context import coder_prompt, extract_code

def core_domain_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 2: Core Domain Specialist generates pure Kotlin shared logic in commonMain."""
    plan = state.get("plan")
    task_id = state.get("task_id", "default")
    if not plan or not plan.shared_contracts:
        return {"files": {}}

    skill_registry = KMPSkillRegistry()
    skill_context = skill_registry.get_skills_for_node("core_domain_node")
    router = HybridModelRouter(task_id=task_id)

    generated_files: Dict[str, KMPFileSpec] = {}
    for spec in plan.shared_contracts:
        prompt = coder_prompt(state, spec, "Implement shared domain file", skill_context, generated_files)
        res = router.invoke([
            SystemMessage(content=CORE_DOMAIN_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        clean_code = extract_code(res.content)

        generated_files[spec.file_path] = KMPFileSpec(
            file_path=spec.file_path,
            source_set=spec.source_set,
            content=clean_code if clean_code else spec.content,
            description=spec.description
        )

    return {
        "files": generated_files,
        "messages": [AIMessage(content=f"Core Domain Agent generated {len(generated_files)} shared files in commonMain.")]
    }
