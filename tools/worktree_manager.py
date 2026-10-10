import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from config import config, REPO_ROOT

class KMPWorktreeManager:
    """Agent 7: Provisions, commits and prunes isolated Git worktrees.

    With a target project, worktrees are cut from that project's repo but stored under this
    repo's `.worktrees/<project>/`, so the project's own checkout is never touched. Finished
    work stays on its `agent/<task-id>` branch for the developer to review and merge.
    """

    def __init__(self, project: Optional[Dict[str, Any]] = None):
        self.project = project or {}
        self.repo_root = Path(self.project.get("path") or REPO_ROOT).resolve()
        self.base_branch = self.project.get("base_branch", "main")
        self.worktrees_dir = config.worktrees_dir / self.project.get("name", "self")
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

    def _git(self, *args, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=cwd or self.repo_root, capture_output=True, text=True)

    def worktree_path(self, task_id: str) -> Path:
        return self.worktrees_dir / task_id

    def project_root(self, task_id: str) -> Path:
        """The Gradle/KMP root inside the task worktree (where generated paths are relative to)."""
        return self.worktree_path(task_id) / self.project.get("gradle_subdir", "")

    def create_worktree(self, task_id: str) -> Path:
        """Creates a dedicated branch and worktree directory for the task; returns the KMP root in it."""
        worktree_path = self.worktree_path(task_id)
        branch_name = f"agent/{task_id}"

        if not worktree_path.exists():
            if not (self.repo_root / ".git").exists():
                if self.project:
                    raise RuntimeError(f"Project '{self.project['name']}' at {self.repo_root} is not a git repository")
                # Fallback for non-git workspaces: create local directory
                worktree_path.mkdir(parents=True, exist_ok=True)
                return self.project_root(task_id)

            res = self._git("worktree", "add", "-b", branch_name, str(worktree_path), self.base_branch)
            if res.returncode != 0:
                # Branch already exists (e.g. resumed task): attach it instead
                res = self._git("worktree", "add", str(worktree_path), branch_name)
                if res.returncode != 0:
                    raise RuntimeError(f"git worktree add failed: {res.stderr.strip()}")

        # Copy git-ignored files the build needs (local.properties, google-services.json, ...)
        for rel in self.project.get("copy_untracked", []):
            src, dst = self.repo_root / rel, worktree_path / rel
            if src.exists() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        return self.project_root(task_id)

    def commit_task_progress(self, task_id: str, commit_message: str) -> bool:
        """Commits changes made by agents inside the task worktree."""
        worktree_path = self.worktree_path(task_id)
        if not worktree_path.exists():
            return False
        self._git("add", "-A", cwd=worktree_path)
        return self._git("commit", "-m", commit_message, cwd=worktree_path).returncode == 0

    def working_diff(self, task_id: str) -> str:
        """Uncommitted changes in the task worktree, including new files (for review before commit)."""
        worktree_path = self.worktree_path(task_id)
        if not worktree_path.exists():
            return ""
        # Intent-to-add makes new files show up in `git diff` without staging their content
        self._git("add", "-A", "--intent-to-add", cwd=worktree_path)
        return self._git("diff", cwd=worktree_path).stdout

    def get_unified_diff(self, task_id: str) -> str:
        """Returns the diff between the task branch and the base branch."""
        res = self._git("diff", f"{self.base_branch}...agent/{task_id}")
        return res.stdout or "No changes detected."

    def remove_worktree(self, task_id: str):
        """Removes the worktree directory but keeps the `agent/<task-id>` branch for review."""
        worktree_path = self.worktree_path(task_id)
        if worktree_path.exists():
            self._git("worktree", "remove", "--force", str(worktree_path))
        self._git("worktree", "prune")

    def merge_and_prune(self, task_id: str, target_branch: str = "main") -> bool:
        """Merges the task branch into target_branch. Only used for the self-hosted (no project) mode."""
        if self.project:
            raise RuntimeError("Refusing to auto-merge into a target project; review the agent branch instead")
        branch_name = f"agent/{task_id}"
        self._git("checkout", target_branch)
        merge_res = self._git("merge", branch_name)
        self.remove_worktree(task_id)
        return merge_res.returncode == 0
