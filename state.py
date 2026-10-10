from typing import Annotated, TypedDict, List, Dict, Optional, Literal, Any
from langchain_core.messages import BaseMessage
import operator
from pydantic import BaseModel, Field

class KMPFileSpec(BaseModel):
    """Represents a file generated or modified in a specific KMP source set."""
    file_path: str = Field(description="Relative path e.g. composeApp/src/commonMain/kotlin/App.kt")
    source_set: str = Field(description="e.g. commonMain, androidMain, iosMain, commonTest")
    content: str
    description: str

class ExpectActualBridge(BaseModel):
    """Represents an expect/actual contract bridge pair."""
    interface_name: str
    expect_declaration: KMPFileSpec
    actual_implementations: Dict[str, KMPFileSpec] = Field(default_factory=dict)

class KMPPlan(BaseModel):
    """The master architectural blueprint produced by Agent 1 (Lead Architect)."""
    feature_name: str
    architecture_overview: str
    target_platforms: List[str] = Field(default_factory=lambda: ["android", "ios", "desktop", "wasmJs"])
    dependencies: List[str] = Field(default_factory=list, description="libs.versions.toml entries")
    shared_contracts: List[KMPFileSpec] = Field(default_factory=list)
    bridges: List[ExpectActualBridge] = Field(default_factory=list)
    ui_screens: List[KMPFileSpec] = Field(default_factory=list)

class CompilerDiagnostic(BaseModel):
    """Structured representation of a Kotlin 2.x compiler error."""
    file_path: str
    line: int
    column: int
    error_message: str
    responsible_agent: Literal["core_domain", "compose_ui", "native_bridge", "build_qa"]
    suggested_fix: Optional[str] = None
    known_episodic_fix: Optional[str] = None

class SecurityReport(BaseModel):
    """OWASP Security inspection report."""
    passed: bool
    violations: List[str] = Field(default_factory=list)
    sanitized_items: List[str] = Field(default_factory=list)

def merge_file_maps(existing: Dict[str, KMPFileSpec], new_files: Dict[str, KMPFileSpec]) -> Dict[str, KMPFileSpec]:
    """Reducer that merges new/updated files into the working state file map."""
    updated = existing.copy() if existing else {}
    if new_files:
        updated.update(new_files)
    return updated

class KMPGraphState(TypedDict):
    """The central state flowing through the LangGraph StateGraph."""
    # Tier 2 Conversation & Node Trajectory History (Append-only)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Task Inputs & Execution Context
    task_id: str
    task_description: str
    target_platforms: List[Literal["android", "ios", "desktop", "wasmJs"]]
    workspace_root: str # KMP/Gradle root inside the isolated Git Worktree
    project_name: str # Key into `projects` in kmp_agent_config.yaml ("" = this repo)
    
    # Architecture Blueprint
    plan: Optional[KMPPlan]
    
    # Active Files (Merged across coder nodes)
    files: Annotated[Dict[str, KMPFileSpec], merge_file_maps]
    
    # Security Gate State
    security_report: Optional[SecurityReport]
    
    # Verification & Compiler Feedback
    build_status: Literal["pending", "success", "failed"]
    build_output_tail: str
    compiler_diagnostics: List[CompilerDiagnostic]
    
    # Fix instructions from the diagnostic agent, fed back into the coder agents on retry
    fix_notes: str

    # Self-Healing Iteration Control
    iteration_count: int
    max_iterations: int
    
    # Dynamic Router Navigation
    next_node: Optional[str]
