"""Shared prompt context so the coder agents build on the target project's existing code."""
import re
from pathlib import Path
from typing import Dict, List, Optional

from state import KMPGraphState, KMPFileSpec

_DECL = re.compile(r"^\s*(?:(?:public|internal|private|data|sealed|enum|abstract|open|expect|actual|suspend|inline|value|@Composable)\s+)*"
                   r"(class|interface|object|fun|typealias)\s+([A-Za-z0-9_<>.]+)", re.MULTILINE)
_MAX_FILE_CHARS = 15000


def project_overview(workspace_root: str, target_platforms: List[str]) -> str:
    """Compact map of the existing Kotlin sources: path, package and top-level declarations."""
    root = Path(workspace_root)
    lines = [
        "### Existing project (paths relative to the KMP root):",
        f"Target platforms: {', '.join(target_platforms)} ONLY — do not create source sets for any other platform.",
    ]
    for kt in sorted(root.glob("*/src/*/kotlin/**/*.kt")):
        rel = kt.relative_to(root).as_posix()
        if "/build/" in rel:
            continue
        try:
            text = kt.read_text(encoding="utf-8")
        except Exception:
            continue
        pkg = re.search(r"^package\s+([\w.]+)", text, re.MULTILINE)
        decls = sorted({name for _, name in _DECL.findall(text)})[:15]
        lines.append(f"- {rel} [{pkg.group(1) if pkg else '?'}]: {', '.join(decls)}")
    return "\n".join(lines) if len(lines) > 2 else ""


def existing_file(workspace_root: str, rel_path: str) -> str:
    path = Path(workspace_root) / rel_path
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    if len(text) > _MAX_FILE_CHARS:
        text = text[:_MAX_FILE_CHARS] + "\n// ... (truncated)"
    return text


def coder_prompt(state: KMPGraphState, spec: KMPFileSpec, task: str, skill_context: str,
                 generated: Optional[Dict[str, KMPFileSpec]] = None) -> str:
    """Builds a coder-agent prompt: the file to write, the existing file (if any), project map,
    the other files written in this task (so code and tests agree) and fix notes."""
    root = state.get("workspace_root", ".")
    parts = [
        f"Feature request: {state.get('task_description', '')}",
        f"{task}: {spec.file_path} (source set: {spec.source_set})\nDescription: {spec.description}",
    ]
    current = existing_file(root, spec.file_path)
    if current:
        parts.append("This file already exists. Return the COMPLETE updated file, preserving existing behaviour:\n"
                     f"```kotlin\n{current}\n```")
    overview = project_overview(root, state.get("target_platforms") or [])
    if overview:
        parts.append(overview + "\nUse these packages and reuse existing types instead of redefining them.")
    siblings = {**(state.get("files") or {}), **(generated or {})}
    siblings.pop(spec.file_path, None)
    if siblings:
        budget, blocks = 40000, []
        for path, other in siblings.items():
            body = other.content if len(other.content) <= budget else other.content[:budget] + "\n// ... (truncated)"
            budget -= len(body)
            blocks.append(f"// {path}\n{body}")
            if budget <= 0:
                break
        parts.append("Other files written in this task — stay consistent with them exactly "
                     "(names, signatures, output formats):\n```kotlin\n" + "\n\n".join(blocks) + "\n```")
    if state.get("fix_notes"):
        parts.append(f"The previous attempt failed to compile. Apply these fixes:\n{state['fix_notes']}")
    parts.append("Return only the Kotlin source for this one file in a single ```kotlin block.")
    parts.append(skill_context)
    return "\n\n".join(p for p in parts if p)


def extract_code(text: str) -> str:
    """Returns the largest fenced code block (or the raw text when there is none)."""
    blocks = re.findall(r"```(?:kotlin|kt)?\s*\n(.*?)```", text, re.DOTALL)
    return max(blocks, key=len).strip() if blocks else text.strip()
