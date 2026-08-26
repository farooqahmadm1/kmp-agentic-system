# 🚀 KMP Agentic System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/Local%20LLM-Ollama-black.svg)](https://ollama.ai)
[![DeepSeek](https://img.shields.io/badge/Cloud%20LLM-DeepSeek%20V3-blueviolet.svg)](https://deepseek.com)
[![KMP](https://img.shields.io/badge/Kotlin-Multiplatform%202.x-purple.svg)](https://kotlinlang.org/docs/multiplatform.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An autonomous, hybrid AI multi-agent software engineering system built on **Lean LangGraph**, combining **DeepSeek Cloud API** (primary reasoning & architecture) with **Local Ollama** (`qwen2.5-coder:14b` fallback & budget protection), grounded in an AST-based Codebase Knowledge Graph powered by **Graphify (`Graphify-Labs/graphify`)**, fortified with **OWASP Dual-Layer Security Guardrails**, isolated via **Git Worktrees**, and persisted with an **Enterprise Session & Time-Travel Engine**, specialized for full-lifecycle **Kotlin Multiplatform (KMP)** and **Compose Multiplatform** development.

---

## 🏛️ System Topology & Workflow

```mermaid
graph TD
    Developer([👨‍💻 Developer / CLI]) --> PreFlight[🛡️ Agent 6: OWASP Pre-Flight Sanitizer & Redactor]
    PreFlight --> RouterNode[🔀 Hybrid Model Router & Token Budget Manager]

    subgraph LLM_Backend ["🤖 Hybrid Intelligence Layer"]
        DeepSeek[⚡ DeepSeek Cloud API<br/><i>Primary: Architect & Deep Logic</i>]
        Ollama[🦙 Local Ollama Engine<br/><i>Fallback: qwen2.5-coder:14b / Offline</i>]
        BudgetTracker[(📊 Token Budget & Quota Ledger)]
        
        DeepSeek -.->|Quota Exceeded / 429 RateLimit / Offline| Ollama
        DeepSeek --> BudgetTracker
        Ollama --> BudgetTracker
    end

    RouterNode --> StateGraphEngine[⚙️ LangGraph StateGraph Engine]

    subgraph Knowledge_Layer ["🕸️ Graphify AST Knowledge Graph (Tier 3)"]
        GraphifyDB[(Graphify Codebase Graph<br/><i>expect/actual map, call graph, blast radius</i>)]
    end

    subgraph Session_Persistence ["💾 Enterprise Session & Checkpointer Engine"]
        SqliteSaver[(SQLite Checkpoint DB<br/><i>thread_id state snapshots</i>)]
        JSONLLogger[(Trajectory JSONL & Diffs)]
    end

    subgraph StateGraphEngine ["🔄 LangGraph Cyclic Workflow"]
        Start([__start__]) --> InitNode[🌳 Agent 7: Init Worktree & Task State]
        InitNode --> ArchNode[🎯 Agent 1: Lead Architect Node<br/><i>Clean KMP Architecture Decomposition</i>]
        
        ArchNode --> HITL_PlanGate{⏸️ HITL Gate 1: Plan Approval}
        HITL_PlanGate -->|Approved| SkillLoader[📚 Progressive Skill Loader]
        HITL_PlanGate -->|Feedback| ArchNode
        
        SkillLoader --> CoreNode[🧠 Agent 2: Core Domain Node<br/><i>commonMain Pure Kotlin / Ktor / Room</i>]
        SkillLoader --> UINode[🎨 Agent 3: Compose UI Node<br/><i>Compose Multiplatform M3 & Resources</i>]
        SkillLoader --> BridgeNode[📱 Agent 4: Native Bridge Node<br/><i>expect/actual iOS/Android/Desktop/Wasm</i>]
        
        CoreNode --> GuardrailNode[🛡️ Agent 6: OWASP Code & AST Guardrail]
        UINode --> GuardrailNode
        BridgeNode --> GuardrailNode
        
        GuardrailNode --> WriteNode[📂 Agent 7: Sandboxed File Writer]
        WriteNode --> GradleNode[⚙️ Agent 8: Isolated Gradle Build & Check]
        
        GradleNode -->|Build Passed (0 Errors)| UIVerifyNode[🖼️ Agent 9: Headless Compose Preview Test]
        UIVerifyNode --> HITL_DiffGate{⏸️ HITL Gate 2: Diff Review}
        HITL_DiffGate -->|Approved| MergeNode[✅ Commit, Merge & Prune Worktree]
        MergeNode --> EndSuccess([__end__ Task Complete])
        
        GradleNode -->|Build Failed & Iterations < Max| DiagNode[🩺 Agent 5: Diagnostic & Self-Healing Node]
        GradleNode -->|Max Iterations Exceeded| EndFail([__end__ Revert & Report Failure])
        
        DiagNode --> QueryEpisodic[🔍 Query Episodic Memory for Known Fixes]
        QueryEpisodic --> RouteFix{Route Targeted Patch}
        RouteFix -->|Domain Logic Error| CoreNode
        RouteFix -->|UI / Resource Error| UINode
        RouteFix -->|Platform Bridge Error| BridgeNode
        
        DiagNode -.->|Save New Working Fix| SaveEpisodic[(💾 Save to Episodic Store)]
    end

    StateGraphEngine <-->|Checkpoint Every Node| SqliteSaver
    StateGraphEngine -->|Log Steps| JSONLLogger
    StateGraphEngine -->|Event Stream| Dashboard[🖥️ Rich Live Terminal Dashboard]
```

---

## 🤖 The 9-Agent Roster

| # | Agent Name | Type | Model / Tech | Core Responsibilities |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **🎯 Lead Architect & Planner** | Cognitive | DeepSeek / `qwen2.5-coder:32b` | Decomposes feature into Clean Architecture layers, identifies existing shared classes via Graphify, and maps `expect`/`actual` bridges. |
| **2** | **🧠 Core Domain Specialist** | Cognitive | `qwen2.5-coder:14b` | Generates pure Kotlin shared logic in `commonMain` (Ktor 3.x, Room KMP/SQLDelight, Coroutines `StateFlow`). |
| **3** | **🎨 Compose UI Specialist** | Cognitive | `qwen2.5-coder:14b` | Implements adaptive Material 3 UI screens and Compose Multiplatform **Resources API** (`Res.string.*`, `Res.drawable.*`). |
| **4** | **📱 Native Bridge Specialist** | Cognitive | `qwen2.5-coder:14b` | Implements `expect` declarations in `commonMain` and platform `actual` code (Android KeyStore, iOS Keychain / `SKIE`, Desktop, Wasm). |
| **5** | **🩺 Diagnostic QA Agent** | Cognitive | `qwen2.5-coder:14b` | Analyzes Kotlin 2.x compiler error logs, matches episodic memory fix recipes, and dispatches targeted diffs. |
| **6** | **🛡️ OWASP Security Guardrail** | Guardian | Deterministic Python / AST | Pre-flight prompt sanitizer, secret redactor, Mobile Top 10 compliance checker, and dependency verification. |
| **7** | **📂 Worktree & File Sandbox** | Guardian | Git Worktree / Pathlib | Provisions `.worktrees/<task-id>`, confines file writes to sandbox, and manages atomic commits and merges. |
| **8** | **⚙️ Gradle Build Runner** | Guardian | Subprocess / Gradle Daemon | Executes isolated `./gradlew check` and extracts structured `CompilerDiagnostic` error logs. |
| **9** | **🖼️ Headless UI Verifier** | Guardian | Compose Desktop Rule / Skiko | Renders and validates `@Preview` composables using headless desktop test harnesses before merge. |

---

## 🛡️ OWASP Dual-Layer Security & Guardrails

1. **Layer 1: Agentic System Security (OWASP Top 10 for LLMs / Agents)**:
   - **LLM01 Prompt Injection Defense**: Delimiter boundary isolation (`<user_task_specification>`).
   - **LLM02 Secret & PII Redactor**: Pre-flight regex & entropy scanner strips API keys and credentials before LLM calls.
   - **LLM06 Excessive Agency Sandboxing**: Strict file I/O boundary confinement within `.worktrees/<task-id>`.
   - **LLM09 Dependency Slopsquatting Protection**: Validates new Gradle dependencies against Maven Central and Google Maven.
   - **LLM10 Token DoS Circuit Breaker**: Caps self-healing iterations (`max_iterations = 5`) and daily token spend.

2. **Layer 2: KMP Application Security (OWASP Mobile Top 10)**:
   - **M1 Secure Storage**: Enforces **Android KeyStore** (`EncryptedSharedPreferences`) and **iOS Keychain Services** (blocks plain `SharedPreferences`).
   - **M4 Safe Data & Serialization**: Parameterized SQL queries and safe `kotlinx.serialization`.
   - **M5 Secure Communication**: Ktor TLS enforcement, certificate pinning, and ATS/NetworkSecurityConfig compliance.

---

## 💾 4-Tier Cognitive Memory & Session Persistence

- **Tier 1 (Ephemeral Scratchpad)**: Raw compiler logs and tool stdout wiped per step.
- **Tier 2 (Task Working State)**: LangGraph `thread_id` checkpoints stored in `.sessions/checkpoints.db`.
- **Tier 3 (Project Codebase Graph)**: Graphify AST Knowledge Graph of the KMP repository.
- **Tier 4 (Episodic Learning Memory)**: SQLite database of past compiler error signatures and verified resolution recipes.

---

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/your-org/kmp-agentic-system.git
cd kmp-agentic-system
pip install -r requirements.txt
```

### 2. Pull Recommended Local Model (Ollama)
```bash
ollama pull qwen2.5-coder:14b
```

### 3. Pre-Flight Health Check
```bash
python3 cli.py health
```

### 4. Scaffold Fresh KMP Project
```bash
python3 cli.py init
```

### 5. Launch an Autonomous Feature Task
```bash
python3 cli.py new-task "Create a shared biometric authentication reader with expect/actual and a Compose UI status card"
```

### 6. Manage Sessions
```bash
python3 cli.py session list
```

---

## 🧪 Testing

Run the full automated test suite:
```bash
python3 -m unittest discover tests
```

---

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.
