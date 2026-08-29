# 💻 CLI & Makefile Reference

## 1. Top-Level CLI Commands (`cli.py`)

### `health`
Runs pre-flight connectivity and status checks on Local Ollama and Cloud LLM providers.
```bash
python3 cli.py health
# Or using make:
make health
```

### `init`
Scaffolds a production-ready Kotlin 2.x + Compose Multiplatform starter project.
```bash
python3 cli.py init --name MySuperApp --package com.example.superapp
# Or using make:
make init
```

### `new-task`
Launches an autonomous feature development lifecycle for a given prompt.
```bash
python3 cli.py new-task "Implement shared biometric authentication with expect/actual and Compose UI"
```

### `tui`
Launches the interactive split-pane Textual terminal dashboard.
```bash
python3 cli.py tui
# Or using make:
make tui
```

### `session list`
Lists all active, paused, and completed development tasks with metadata.
```bash
python3 cli.py session list
```

---

## 2. Makefile Shortcuts

| Command | Action |
| :--- | :--- |
| `make install` | Upgrades pip and installs all dependencies from `requirements.txt`. |
| `make test` | Runs the automated unit test suite. |
| `make health` | Checks local Ollama and configured cloud model status. |
| `make init` | Generates a full starter KMP repository. |
| `make tui` | Launches the interactive Textual TUI dashboard. |
| `make docker-up` | Starts the multi-agent system and Ollama container mesh. |
| `make docker-down` | Stops all Docker containers. |
| `make clean` | Removes cache and temporary test directories. |
