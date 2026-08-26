from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from state import KMPGraphState, SecurityReport
from security.secret_redactor import SecretRedactor
from security.dependency_verifier import DependencyVerifier

def guardrail_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 6: OWASP AST & Security Guardrail validation node."""
    files = state.get("files", {})
    plan = state.get("plan")
    violations: List[str] = []

    # 1. Check generated files for hardcoded secrets & forbidden plain SharedPreferences
    for path, spec in files.items():
        _, detected_secrets = SecretRedactor.redact(spec.content)
        if detected_secrets:
            violations.append(f"Hardcoded credentials detected in '{path}': {detected_secrets}")
        
        if "commonMain" in path:
            if "android.content.Context" in spec.content:
                violations.append(f"Forbidden platform import 'android.content.Context' in commonMain file: {path}")
            if "java.io." in spec.content:
                violations.append(f"Forbidden JVM-only import 'java.io.*' in commonMain file: {path}")

    # 2. Check dependencies against slopsquatting registry
    if plan and plan.dependencies:
        for dep in plan.dependencies:
            ok, msg = DependencyVerifier.verify_dependency(dep)
            if not ok:
                violations.append(f"Dependency Alert: {msg}")

    passed = len(violations) == 0
    report = SecurityReport(passed=passed, violations=violations)

    return {
        "security_report": report,
        "messages": [AIMessage(content=f"OWASP Security Guardrail: {'PASSED' if passed else 'VIOLATIONS DETECTED: ' + str(violations)}")]
    }
