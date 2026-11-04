from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from state import KMPGraphState, KMPFileSpec
from models.hybrid_router import HybridModelRouter
from models.prompt_templates import COMPOSE_UI_SYSTEM_PROMPT
from skills.skill_registry import KMPSkillRegistry
from nodes.project_context import coder_prompt, extract_code, files_to_regenerate, keep_or_regenerate

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
    targets = files_to_regenerate(state)  # on retries, only the files that need fixing
    for spec in plan.ui_screens:
        kept = keep_or_regenerate(state, spec, targets)
        if kept:
            generated_files[spec.file_path] = kept
            continue
        prompt = coder_prompt(state, spec, "Implement Compose Multiplatform UI", skill_context, generated_files)
        res = router.invoke([
            SystemMessage(content=COMPOSE_UI_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])

        clean_code = extract_code(res.content)
        previous = (state.get("files") or {}).get(spec.file_path)

        generated_files[spec.file_path] = KMPFileSpec(
            file_path=spec.file_path,
            source_set=spec.source_set,
            content=clean_code or (previous.content if previous else spec.content),
            description=spec.description
        )

    return {
        "files": generated_files,
        "messages": [AIMessage(content=f"Compose UI Agent generated {len(generated_files)} UI screens.")]
    }
