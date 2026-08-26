from typing import Dict, Any, List
from memory.graphify_store import GraphifyASTStore

class GraphifyKMPTool:
    """Tool allowing LangGraph agents to query the codebase AST knowledge graph."""

    def __init__(self, workspace_root: str):
        self.store = GraphifyASTStore(workspace_root)
        self.store.scan_and_index()

    def find_missing_bridges(self, platform: str) -> List[str]:
        """Finds all expect declarations lacking actual implementations on a target platform."""
        return self.store.get_missing_actuals(platform)

    def get_subgraph_context(self, symbols: List[str]) -> str:
        """Retrieves 1-hop AST context for the specified symbols."""
        return self.store.get_context_subgraph(symbols)
