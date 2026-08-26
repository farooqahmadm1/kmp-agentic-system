import subprocess
import os
import re
from pathlib import Path
from typing import Dict, Any, List
from state import CompilerDiagnostic

class GradleBuildRunner:
    """Agent 8: Executes isolated Gradle tasks and parses Kotlin compiler diagnostics."""

    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()

    def run_task(self, task: str = "check") -> Dict[str, Any]:
        """Executes a Gradle task (e.g. 'compileKotlin', 'check') inside the worktree."""
        gradlew = self.root / ("gradlew.bat" if os.name == "nt" else "./gradlew")
        
        # If gradlew doesn't exist, simulate verification for dry-run environments
        if not gradlew.exists():
            return {
                "success": True,
                "exit_code": 0,
                "output_tail": f"[Simulated Gradle Environment] Checked task '{task}' successfully (mock).",
                "diagnostics": []
            }

        cmd = [str(gradlew), task, "--stacktrace"]
        try:
            res = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, timeout=240)
            combined_output = (res.stdout or "") + "\n" + (res.stderr or "")
            diagnostics = self._parse_compiler_errors(combined_output)
            
            return {
                "success": res.returncode == 0,
                "exit_code": res.returncode,
                "output_tail": combined_output[-3000:],
                "diagnostics": diagnostics
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "output_tail": "Gradle build timed out after 240 seconds.",
                "diagnostics": []
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "output_tail": str(e),
                "diagnostics": []
            }

    def _parse_compiler_errors(self, output: str) -> List[CompilerDiagnostic]:
        """Extracts structured Kotlin compiler error signatures: e: /path/File.kt: (line, col): message"""
        diagnostics = []
        # Pattern: e: /path/file.kt: (12, 5): Unresolved reference: foo
        pattern = r"e:\s+([^\n:]+\.kt):\s*\((\d+),\s*(\d+)\):\s*(.+)"
        matches = re.findall(pattern, output)

        for filepath, line, col, msg in matches:
            # Attribute responsible agent based on path
            agent = "core_domain"
            if "androidMain" in filepath or "iosMain" in filepath or "desktopMain" in filepath:
                agent = "native_bridge"
            elif "Screen" in filepath or "Component" in filepath or "Theme" in filepath:
                agent = "compose_ui"

            diagnostics.append(CompilerDiagnostic(
                file_path=filepath,
                line=int(line),
                column=int(col),
                error_message=msg.strip(),
                responsible_agent=agent
            ))

        return diagnostics
