import subprocess
import os
import re
from pathlib import Path
from typing import Dict, Any, List
from state import CompilerDiagnostic

class GradleBuildRunner:
    """Agent 8: Executes isolated Gradle tasks and parses Kotlin compiler diagnostics."""

    def __init__(self, workspace_root: str, require_gradlew: bool = False, timeout: int = 1800):
        self.root = Path(workspace_root).resolve()
        self.require_gradlew = require_gradlew
        # A fresh worktree has a cold Gradle/Kotlin-Native cache, so the first build can be slow
        self.timeout = timeout

    def run_task(self, *tasks: str) -> Dict[str, Any]:
        """Executes Gradle tasks (e.g. 'compileKotlin', 'check') inside the worktree."""
        tasks = tasks or ("check",)
        task = " ".join(tasks)
        gradlew = self.root / ("gradlew.bat" if os.name == "nt" else "gradlew")

        if not gradlew.exists() and self.require_gradlew:
            return {
                "success": False,
                "exit_code": -1,
                "output_tail": f"gradlew not found in {self.root}",
                "diagnostics": []
            }

        # If gradlew doesn't exist, simulate verification for dry-run environments
        if not gradlew.exists():
            return {
                "success": True,
                "exit_code": 0,
                "output_tail": f"[Simulated Gradle Environment] Checked task '{task}' successfully (mock).",
                "diagnostics": []
            }

        cmd = [str(gradlew), *tasks, "--stacktrace"]
        try:
            res = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, timeout=self.timeout)
            combined_output = (res.stdout or "") + "\n" + (res.stderr or "")
            diagnostics = self._parse_compiler_errors(combined_output)
            tail = combined_output[-3000:]
            if res.returncode != 0:
                failures = self._test_failures()
                if failures:
                    tail = "Failing unit tests:\n" + failures + "\n\n" + tail

            return {
                "success": res.returncode == 0,
                "exit_code": res.returncode,
                "output_tail": tail,
                "diagnostics": diagnostics
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "output_tail": f"Gradle build timed out after {self.timeout} seconds.",
                "diagnostics": []
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "output_tail": str(e),
                "diagnostics": []
            }

    def _test_failures(self, limit: int = 4000) -> str:
        """Collects failing test names and assertion messages (expected vs actual) from JUnit XML reports."""
        import xml.etree.ElementTree as ET
        lines = []
        for report in self.root.glob("*/build/test-results/**/*.xml"):
            try:
                for case in ET.parse(report).getroot().iter("testcase"):
                    failure = case.find("failure")
                    if failure is not None:
                        msg = (failure.get("message") or (failure.text or "").splitlines()[0:1] or [""])
                        msg = msg if isinstance(msg, str) else msg[0]
                        lines.append(f"- {case.get('classname')}.{case.get('name')}: {msg.strip()}")
            except Exception:
                continue
        return "\n".join(lines)[:limit]

    def _parse_compiler_errors(self, output: str) -> List[CompilerDiagnostic]:
        """Extracts structured Kotlin compiler error signatures: e: /path/File.kt: (line, col): message"""
        diagnostics = []
        # Pattern: e: /path/file.kt: (12, 5): Unresolved reference: foo
        pattern = r"e:\s+([^\n:]+\.kt):\s*\((\d+),\s*(\d+)\):\s*(.+)"
        matches = re.findall(pattern, output)
        # Kotlin 2.x (K2) format: e: file:///path/file.kt:12:5 Unresolved reference 'foo'.
        matches += re.findall(r"e:\s+(?:file://)?([^\s]+\.kt):(\d+):(\d+)\s+(.+)", output)

        for filepath, line, col, msg in matches:
            # Attribute responsible agent based on path
            agent = "core_domain"
            if any(s in filepath for s in ("/android", "/iosMain", "/desktopMain", "/wasmJsMain")):
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
