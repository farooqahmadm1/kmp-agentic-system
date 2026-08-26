from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from state import KMPGraphState, KMPFileSpec
from models.hybrid_router import HybridModelRouter
from models.prompt_templates import COMPOSE_UI_SYSTEM_PROMPT
from skills.skill_registry import KMPSkillRegistry

def compose_ui_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 3: Compose UI Specialist generates declarative Compose Multiplatform UI."""
    plan = state.get("plan")
    task_id = state.get("task_id", "default")
    if not plan or not plan.ui_screens:
        return {"files": {}}

    skill_registry = KMPSkillRegistry()
    skill_context = skill_registry.get_skills_for_node("compose_ui_node")
    router = HybridModelRouter(task_id=task_id)

    generated_files: Dict[str, KMPFileSpec] = {}
    for spec in plan.ui_screens:
        prompt = f"Implement Compose Multiplatform UI: {spec.file_path}\nDescription: {spec.description}\n\n{skill_context}"
        res = router.invoke([
            SystemMessage(content=COMPOSE_UI_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        clean_code = res.content
        if "```kotlin" in clean_code:
            clean_code = clean_code.split("```kotlin")[1].split("```")[0].strip()
        elif "```" in clean_code:
            clean_code = clean_code.split("```")[1].split("```")[0].strip()

        generated_files[spec.file_path] = KMPFileSpec(
            file_path=spec.file_path,
            source_set=spec.source_set,
            content=clean_code if clean_code else spec.content,
            description=spec.description
        )

    return {
        "files": generated_files,
        "messages": [AIMessage(content=f"Compose UI Agent generated {len(generated_files)} UI screens.")]
    }
