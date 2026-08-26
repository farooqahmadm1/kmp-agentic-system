from langgraph.graph import StateGraph, START, END
from typing import Literal

from state import KMPGraphState
from config import config
from memory.session_manager import SessionManager
from nodes.init_node import init_node
from nodes.architect_node import architect_node
from nodes.core_domain_node import core_domain_node
from nodes.compose_ui_node import compose_ui_node
from nodes.native_bridge_node import native_bridge_node
from nodes.guardrail_node import guardrail_node
from nodes.file_writer_node import file_writer_node
from nodes.gradle_build_node import gradle_build_node
from nodes.ui_verify_node import ui_verify_node
from nodes.diagnostic_node import diagnostic_node
from nodes.finalize_node import finalize_node

def route_after_gradle(state: KMPGraphState) -> Literal["ui_verify_node", "diagnostic_node", "finalize_node"]:
    """Conditional router determining whether build succeeded, failed (self-healing), or reached max retries."""
    status = state.get("build_status", "pending")
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", config.max_self_healing_iterations)

    if status == "success":
        return "ui_verify_node"
    elif iteration < max_iter:
        return "diagnostic_node"
    else:
        return "finalize_node" # Exceeded iterations, finalize/abort

def create_kmp_graph(checkpointer=None):
    """Assembles the complete cyclic StateGraph for KMP multi-agent development."""
    workflow = StateGraph(KMPGraphState)

    # 1. Register all 9 agent/tool nodes
    workflow.add_node("init_node", init_node)
    workflow.add_node("architect_node", architect_node)
    workflow.add_node("core_domain_node", core_domain_node)
    workflow.add_node("compose_ui_node", compose_ui_node)
    workflow.add_node("native_bridge_node", native_bridge_node)
    workflow.add_node("guardrail_node", guardrail_node)
    workflow.add_node("file_writer_node", file_writer_node)
    workflow.add_node("gradle_build_node", gradle_build_node)
    workflow.add_node("ui_verify_node", ui_verify_node)
    workflow.add_node("diagnostic_node", diagnostic_node)
    workflow.add_node("finalize_node", finalize_node)

    # 2. Build graph edges
    workflow.add_edge(START, "init_node")
    workflow.add_edge("init_node", "architect_node")
    
    # After architect, route to parallel coder nodes
    workflow.add_edge("architect_node", "core_domain_node")
    workflow.add_edge("core_domain_node", "compose_ui_node")
    workflow.add_edge("compose_ui_node", "native_bridge_node")
    
    # After coder nodes, pass through OWASP guardrail
    workflow.add_edge("native_bridge_node", "guardrail_node")
    workflow.add_edge("guardrail_node", "file_writer_node")
    workflow.add_edge("file_writer_node", "gradle_build_node")

    # Conditional router after Gradle build
    workflow.add_conditional_edges(
        "gradle_build_node",
        route_after_gradle,
        {
            "ui_verify_node": "ui_verify_node",
            "diagnostic_node": "diagnostic_node",
            "finalize_node": "finalize_node"
        }
    )

    # Self-healing loop edge: diagnostic routes back to coder nodes
    workflow.add_edge("diagnostic_node", "core_domain_node")

    # Finalize flow
    workflow.add_edge("ui_verify_node", "finalize_node")
    workflow.add_edge("finalize_node", END)

    # 3. Compile graph with checkpointer and HITL interrupt gates
    session_mgr = SessionManager()
    checkpointer_inst = checkpointer or session_mgr.get_checkpointer()
    
    interrupt_nodes = []
    if config.hitl_plan_approval:
        interrupt_nodes.append("core_domain_node") # Interrupt before writing code to approve plan
    if config.hitl_diff_review:
        interrupt_nodes.append("finalize_node") # Interrupt before merge to inspect diff

    return workflow.compile(
        checkpointer=checkpointer_inst,
        interrupt_before=interrupt_nodes if interrupt_nodes else None
    )
