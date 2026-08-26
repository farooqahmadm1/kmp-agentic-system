from typing import Dict, Any
from langchain_core.messages import AIMessage
from state import KMPGraphState
from tools.ui_preview_runner import UIPreviewVerifier

def ui_verify_node(state: KMPGraphState) -> Dict[str, Any]:
    """Agent 9: Headless Compose Multiplatform preview and UI structure verification."""
    workspace_root = state.get("workspace_root", ".")
    verifier = UIPreviewVerifier(workspace_root)
    res = verifier.verify_previews()

    return {
        "messages": [AIMessage(content=f"UI Preview Verifier: {res['message']}")]
    }
