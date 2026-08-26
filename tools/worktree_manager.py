import subprocess
from pathlib import Path
from typing import Optional

from config import config
from security.path_sandbox import PathSandbox

class KMPWorktreeManager:
    """Agent 7: Provisions, commits, merges, and prunes isolated Git worktrees."""

    def __init__(self, repo_root: Optional[str] = None):
        self.repo_root = Path(repo_root or ".").resolve()
        self.worktrees_dir = self.repo_root / config.worktrees_dir
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, task_id: str, base_branch: str = "main") -> Path:
        """Creates a dedicated branch and worktree directory for the task."""
        worktree_path = self.worktrees_dir / task_id
        branch_name = f"agent/{task_id}"

        if worktree_path.exists():
            return worktree_path

        # Check if git repository is initialized
        if not (self.repo_root / ".git").exists():
            # Fallback for non-git workspaces: create local directory
            worktree_path.mkdir(parents=True, exist_ok=True)
            return worktree_path

        try:
            cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_path)]
            res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)
            if res.returncode != 0 and "already exists" not in res.stderr:
                # If branch already exists, add without -b
                cmd_existing = ["git", "worktree", "add", str(worktree_path), branch_name]
                subprocess.run(cmd_existing, cwd=self.repo_root, capture_output=True, text=True)
        except Exception:
            worktree_path.mkdir(parents=True, exist_ok=True)

        return worktree_path

    def commit_task_progress(self, task_id: str, commit_message: str):
        """Commits changes made by agents inside the task worktree."""
        worktree_path = self.worktrees_dir / task_id
        if not worktree_path.exists():
            return

        subprocess.run(["git", "add", "."], cwd=worktree_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=worktree_path, capture_output=True)

    def get_unified_diff(self, task_id: str) -> str:
        """Returns the unified diff between the worktree branch and main."""
        worktree_path = self.worktrees_dir / task_id
        if not worktree_path.exists():
            return ""
        res = subprocess.run(["git", "diff", "HEAD~1"], cwd=worktree_path, capture_output=True, text=True)
        return res.stdout or "No changes detected."

    def merge_and_prune(self, task_id: str, target_branch: str = "main") -> bool:
        """Merges passing worktree branch into main and prunes the worktree directory."""
        worktree_path = self.worktrees_dir / task_id
        branch_name = f"agent/{task_id}"

        # 1. Merge into target branch
        subprocess.run(["git", "checkout", target_branch], cwd=self.repo_root, capture_output=True)
        merge_res = subprocess.run(["git", "merge", branch_name], cwd=self.repo_root, capture_output=True, text=True)

        # 2. Prune worktree
        if worktree_path.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=self.repo_root, capture_output=True)
            subprocess.run(["git", "worktree", "prune"], cwd=self.repo_root, capture_output=True)

        return merge_res.returncode == 0
