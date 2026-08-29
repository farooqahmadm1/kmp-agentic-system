# 🏛️ Architecture & System Specification

## 1. System Philosophy & Objectives
The **KMP Agentic System** is an autonomous, hybrid multi-agent engineering platform designed specifically for **Kotlin Multiplatform (KMP)** and **Compose Multiplatform** development. It combines the reasoning strengths of top-tier cloud models with the data privacy and zero cost of local offline LLMs.

---

## 2. The 9-Agent Hybrid Roster

```mermaid
graph TD
    subgraph CognitiveAgents ["🧠 5 Cognitive (LLM) Specialists"]
        A1["🎯 Agent 1: Lead Architect<br/><i>Clean Architecture Decomposition</i>"]
        A2["🧠 Agent 2: Core Domain Specialist<br/><i>commonMain Pure Kotlin / Ktor / Room</i>"]
        A3["🎨 Agent 3: Compose UI Specialist<br/><i>Material 3 & Compose Resources API</i>"]
        A4["📱 Agent 4: Native Bridge Specialist<br/><i>expect/actual iOS/Android/Desktop/Wasm</i>"]
        A5["🩺 Agent 5: Diagnostic QA Agent<br/><i>Compiler Self-Healing & Episodic Memory</i>"]
    end

    subgraph GuardianAgents ["🛡️ 4 Deterministic Guardian Agents"]
        G6["🛡️ Agent 6: OWASP Guardrail<br/><i>Sanitization, Redaction, M1-M10 AST checks</i>"]
        G7["📂 Agent 7: Sandboxed Worktree Manager<br/><i>Git Worktree Isolation & File Confinement</i>"]
        G8["⚙️ Agent 8: Gradle Build Runner<br/><i>Isolated Gradle Daemon Execution</i>"]
        G9["🖼️ Agent 9: Headless UI Verifier<br/><i>Compose Desktop @Preview Test Harness</i>"]
    end
```

---

## 3. 4-Tier Cognitive Memory Hierarchy

```mermaid
graph LR
    T1["Tier 1: Ephemeral Scratchpad<br/><i>Raw compiler logs, stdout, wiped per step</i>"]
    T2["Tier 2: Task Working State<br/><i>LangGraph thread_id SQLite checkpoints</i>"]
    T3["Tier 3: Project Codebase Graph<br/><i>Graphify AST expect/actual linkage map</i>"]
    T4["Tier 4: Episodic Learning Memory<br/><i>SQLite database of compiler error recipes</i>"]

    T1 --> T2 --> T3 --> T4
```

1. **Tier 1 (Ephemeral Scratchpad)**: Raw compiler logs, stdout, and tool outputs stored in memory during node execution.
2. **Tier 2 (Task Working State)**: Stateful checkpoints in SQLite (`.sessions/checkpoints.db`) indexed by `thread_id`. Supports time-travel rewinds and session forking.
3. **Tier 3 (Project Codebase Graph)**: AST knowledge graph powered by **Graphify (`Graphify-Labs/graphify`)** mapping `expect` contracts to platform `actual` source files.
4. **Tier 4 (Episodic Learning Memory)**: Evolutionary SQLite knowledge base of resolved compiler errors, root causes, and verified fix recipes.

---

## 4. Hybrid Cloud-Local Model Gateway

```mermaid
graph TD
    Node[Agent Node] --> Router[Hybrid Router]
    Router --> QuotaCheck{Daily Quota Exceeded?}
    
    QuotaCheck -->|No| CloudAttempt[Cloud LLM: Claude / Gemini / DeepSeek]
    QuotaCheck -->|Yes| LocalOllama[Local Ollama: qwen2.5-coder:14b]
    
    CloudAttempt -->|Success| RecordUsage[Record in token_budget.db]
    CloudAttempt -->|429 RateLimit / Offline Error| LocalOllama
    LocalOllama --> RecordUsage
```

- **Cloud Primary**: Supports **Anthropic Claude 3.5 Sonnet**, **Google Gemini 2.0 / 1.5**, and **DeepSeek V3 / R1**.
- **Local Fallback**: Zero-downtime automatic fallback to **Ollama (`qwen2.5-coder:14b`)**.
- **Ledger Tracking**: Tracks daily token burn and estimated cost in SQLite (`token_budget.db`).
