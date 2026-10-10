import json
import os
import shutil
import subprocess
import tempfile
from typing import List

from langchain_core.messages import BaseMessage, SystemMessage, AIMessage


def _split_messages(messages: List[BaseMessage]):
    """Separates system prompts from the conversation and flattens the rest into a transcript."""
    system_parts, convo_parts = [], []
    for msg in messages:
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        if isinstance(msg, SystemMessage):
            system_parts.append(content)
        elif isinstance(msg, AIMessage):
            convo_parts.append(f"[Assistant]\n{content}")
        else:
            convo_parts.append(content)
    return "\n\n".join(system_parts), "\n\n".join(convo_parts)


class _SubscriptionCLI:
    """Base for providers that shell out to a logged-in vendor CLI instead of using an API key."""

    binary: str = ""
    # API-key env vars removed so the CLI falls back to the account login (subscription)
    strip_env: tuple = ()

    def __init__(self, model: str, timeout: int = 600):
        if not shutil.which(self.binary):
            raise RuntimeError(f"`{self.binary}` CLI not found on PATH")
        self.model = model
        self.timeout = timeout

    def _run(self, args: List[str], stdin: str) -> dict:
        env = {k: v for k, v in os.environ.items() if k not in self.strip_env}
        # Run from an empty dir so project context files (CLAUDE.md / GEMINI.md) don't leak in
        with tempfile.TemporaryDirectory() as cwd:
            proc = subprocess.run(
                [self.binary, *args], input=stdin, capture_output=True,
                text=True, timeout=self.timeout, env=env, cwd=cwd
            )
        if proc.returncode != 0:
            raise RuntimeError(f"{self.binary} exited {proc.returncode}: {(proc.stderr or proc.stdout)[-500:]}")
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"{self.binary} returned non-JSON output: {proc.stdout[-500:]}")


class ClaudeCodeCLI(_SubscriptionCLI):
    """Claude via `claude -p`, billed against the Claude Pro/Max subscription Claude Code is logged into."""

    binary = "claude"
    strip_env = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")

    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        system, prompt = _split_messages(messages)
        args = ["-p", "--output-format", "json", "--model", self.model,
                "--tools", "", "--no-session-persistence"]
        if system:
            args += ["--system-prompt", system]
        data = self._run(args, prompt)
        if data.get("is_error"):
            raise RuntimeError(f"claude error: {data.get('result')}")
        usage = data.get("usage", {}) or {}
        # Most of the prompt is usually served from Claude's prompt cache; count it as input too
        input_tokens = sum(usage.get(k, 0) or 0 for k in
                           ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        output_tokens = usage.get("output_tokens", 0) or 0
        return AIMessage(
            content=data.get("result", ""),
            usage_metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
        )


class GeminiCLI(_SubscriptionCLI):
    """Gemini via `gemini -p`, using the Google account (Google AI Pro) the Gemini CLI is logged into."""

    binary = "gemini"
    strip_env = ("GEMINI_API_KEY", "GOOGLE_API_KEY")

    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        system, prompt = _split_messages(messages)
        # Gemini CLI has no system-prompt flag; prepend it to the input
        full_prompt = f"{system}\n\n---\n\n{prompt}" if system else prompt
        # plan mode = read-only, so the model can't edit files or run commands
        args = ["-p", "", "-o", "json", "--approval-mode", "plan", "--skip-trust"]
        if self.model:  # empty = let the Gemini CLI pick its default model
            args += ["-m", self.model]
        data = self._run(args, full_prompt)
        if data.get("error"):
            raise RuntimeError(f"gemini error: {data['error']}")
        tokens = {"input_tokens": 0, "output_tokens": 0}
        for m in ((data.get("stats") or {}).get("models") or {}).values():
            t = m.get("tokens", {}) or {}
            tokens["input_tokens"] += t.get("prompt", 0)
            tokens["output_tokens"] += t.get("candidates", 0)
        tokens["total_tokens"] = tokens["input_tokens"] + tokens["output_tokens"]
        return AIMessage(content=data.get("response", ""), usage_metadata=tokens)
