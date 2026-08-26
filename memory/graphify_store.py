import re
from pathlib import Path
from typing import Dict, Any, List, Optional

class GraphifyASTStore:
    """Tier 3: Graphify AST Codebase Knowledge Graph Adapter for Kotlin Multiplatform."""

    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root)
        self.expect_actual_map: Dict[str, Dict[str, str]] = {}
        self.class_hierarchy: Dict[str, List[str]] = {}
        self.call_graph: Dict[str, List[str]] = {}

    def scan_and_index(self):
        """Extracts AST symbols, expect/actual contracts, and call hierarchies from Kotlin files."""
        if not self.root.exists():
            return

        for kt_file in self.root.glob("**/*.kt"):
            try:
                content = kt_file.read_text(encoding="utf-8")
                rel_path = str(kt_file.relative_to(self.root))
                self._index_file(rel_path, content)
            except Exception:
                continue

    def _index_file(self, rel_path: str, content: str):
        # 1. Detect 'expect' declarations
        expect_matches = re.findall(r"expect\s+(class|interface|fun|val)\s+([A-Za-z0-9_]+)", content)
        for kind, name in expect_matches:
            if name not in self.expect_actual_map:
                self.expect_actual_map[name] = {}
            self.expect_actual_map[name]["expect"] = rel_path

        # 2. Detect 'actual' declarations
        actual_matches = re.findall(r"actual\s+(class|interface|fun|val)\s+([A-Za-z0-9_]+)", content)
        for kind, name in actual_matches:
            if name not in self.expect_actual_map:
                self.expect_actual_map[name] = {}
            # Infer platform from source set path
            platform = "common"
            for p in ("androidMain", "iosMain", "desktopMain", "wasmJsMain"):
                if p in rel_path:
                    platform = p.replace("Main", "")
                    break
            self.expect_actual_map[name][platform] = rel_path

    def get_missing_actuals(self, target_platform: str) -> List[str]:
        """Finds expect declarations lacking an actual implementation for a specific platform."""
        missing = []
        for name, impls in self.expect_actual_map.items():
            if "expect" in impls and target_platform not in impls:
                missing.append(name)
        return missing

    def get_context_subgraph(self, query_symbols: List[str]) -> str:
        """Returns a compact 1-hop subgraph string for the given query symbols to save tokens."""
        lines = ["### Graphify AST Codebase Context:"]
        for sym in query_symbols:
            if sym in self.expect_actual_map:
                impls = self.expect_actual_map[sym]
                lines.append(f"- Contract '{sym}':")
                for plat, path in impls.items():
                    lines.append(f"    * {plat}: {path}")
        return "\n".join(lines) if len(lines) > 1 else "No existing AST linkages found."
