from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from state import KMPGraphState, SecurityReport
from config import config
from security.secret_redactor import SecretRedactor
from security.dependency_verifier import DependencyVerifier
from security.path_sandbox import PathSandbox

def guardrail_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 6: OWASP AST & Security Guardrail validation node.

    Nothing is written to disk unless this passes (see `route_after_guardrail` in graph.py).
    Content violations are sent back to the coder agents as fix notes; path violations can't be
    fixed by regenerating code, so they abort the task.
    """
    files = state.get("files", {})
    plan = state.get("plan")
    workspace_root = state.get("workspace_root", ".")
    project = config.get_project(state.get("project_name", ""))
    allowed = project.get("allowed_paths") or None
    violations: List[str] = []
    fixable = True

    for path, spec in files.items():
        # 1. File location: inside the worktree and within the allowed source sets
        try:
            PathSandbox.validate_safe_path(path, workspace_root)
            inside = True
        except PermissionError:
            inside = False
        if not inside or not PathSandbox.is_source_file_allowed(path, allowed):
            violations.append(f"File path not allowed for agent writes: '{path}'")
            fixable = False
            continue

        # 2. Hardcoded secrets & platform leaks in commonMain
        _, detected_secrets = SecretRedactor.redact(spec.content)
        if detected_secrets:
            violations.append(f"Hardcoded credentials detected in '{path}': {detected_secrets}")

        if "commonMain" in path:
            if "android.content.Context" in spec.content:
                violations.append(f"Forbidden platform import 'android.content.Context' in commonMain file: {path}")
            if "java.io." in spec.content:
                violations.append(f"Forbidden JVM-only import 'java.io.*' in commonMain file: {path}")

    # 3. Dependencies outside the trusted registry need a human look, but don't block the build
    warnings: List[str] = []
    if plan and plan.dependencies:
        for dep in plan.dependencies:
            ok, msg = DependencyVerifier.verify_dependency(dep)
            if not ok:
                warnings.append(f"Dependency Alert: {msg}")

    passed = len(violations) == 0
    report = SecurityReport(passed=passed, violations=violations, fixable=fixable, warnings=warnings)

    update: Dict[str, Any] = {"security_report": report}
    if passed:
        summary = "PASSED" + (f" with {len(warnings)} warning(s): {warnings}" if warnings else "")
    else:
        summary = "VIOLATIONS DETECTED: " + str(violations)
        if fixable:
            # Feed the violations back to the coder agents as the next attempt's fix notes
            update["iteration_count"] = state.get("iteration_count", 0) + 1
            update["fix_notes"] = ("The security guardrail rejected the previous attempt. Fix these issues:\n- "
                                   + "\n- ".join(violations))
    update["messages"] = [AIMessage(content=f"OWASP Security Guardrail: {summary}")]
    return update
