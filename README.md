# 🚀 KMP Agentic System

[![CI Suite](https://github.com/farooqahmadm1/kmp-agentic-system/actions/workflows/ci.yml/badge.svg)](https://github.com/farooqahmadm1/kmp-agentic-system/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/Local%20LLM-Ollama-black.svg)](https://ollama.ai)
[![Claude](https://img.shields.io/badge/Cloud%20LLM-Claude%203.5%20Sonnet-coral.svg)](https://anthropic.com)
[![Gemini](https://img.shields.io/badge/Cloud%20LLM-Gemini%202.0%20%2F%201.5-blue.svg)](https://aistudio.google.com)
[![DeepSeek](https://img.shields.io/badge/Cloud%20LLM-DeepSeek%20V3%20%2F%20R1-blueviolet.svg)](https://deepseek.com)
[![KMP](https://img.shields.io/badge/Kotlin-Multiplatform%202.x-purple.svg)](https://kotlinlang.org/docs/multiplatform.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An autonomous, hybrid AI multi-agent software engineering system built on **Lean LangGraph**, combining **Cloud Models (Claude 3.5 Sonnet, Gemini 2.0/1.5 Pro, DeepSeek V3/R1)** with **Local Ollama** (`qwen2.5-coder:14b` fallback & budget protection), grounded in an AST-based Codebase Knowledge Graph powered by **Graphify (`Graphify-Labs/graphify`)**, fortified with **OWASP Dual-Layer Security Guardrails**, isolated via **Git Worktrees**, equipped with a **Production KMP Scaffolder**, containerized via **Docker**, and persisted with an **Enterprise Session & Time-Travel Engine**, specialized for full-lifecycle **Kotlin Multiplatform (KMP)** and **Compose Multiplatform** development.

---

## 🔑 Connecting Your Accounts (Claude, Gemini, DeepSeek, Ollama)

You can use this system with your existing **Google Gemini account**, **Anthropic Claude account**, **DeepSeek account**, or 100% locally with **Ollama**:

### 1. Google Gemini (Google AI Studio - Free Tier Available)
If you have a Google Account or Gemini Advanced subscription, you can generate an API key via Google AI Studio without credit card fees:
1. Visit **[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)** and sign in with your Google account.
2. Click **"Create API key"**.
3. Set your environment variable:
   ```bash
   export GEMINI_API_KEY="AIzaSy..."
   ```
4. In `kmp_agent_config.yaml`, set:
   ```yaml
   models:
     cloud_provider: "gemini"
     gemini_model: "gemini-2.0-flash"  # or "gemini-1.5-pro"
   ```

---

### 2. Anthropic Claude 3.5 Sonnet (Anthropic Console)
If you use Claude Pro or have an Anthropic developer account:
1. Visit **[https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)**.
2. Click **"Create Key"** and copy your `sk-ant-...` key.
3. Set your environment variable:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```
4. In `kmp_agent_config.yaml`, set:
   ```yaml
   models:
     cloud_provider: "anthropic"
     anthropic_model: "claude-3-5-sonnet-latest"
   ```

---

### 3. DeepSeek (DeepSeek Platform)
1. Visit **[https://platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)**.
2. Create an API key (`sk-...`).
3. Set your environment variable:
   ```bash
   export DEEPSEEK_API_KEY="sk-..."
   ```
4. In `kmp_agent_config.yaml`, set:
   ```yaml
   models:
     cloud_provider: "deepseek"
     deepseek_model: "deepseek-chat"  # or "deepseek-reasoner"
   ```

---

### 4. 100% Free Local Offline Mode (Ollama)
If you do not want to use any cloud provider or API keys:
1. Install and start [Ollama](https://ollama.ai).
2. Pull the recommended local coding model:
   ```bash
   ollama pull qwen2.5-coder:14b
   ```
3. The system automatically runs locally without needing any API keys!

---

## 🏛️ System Topology & Workflow

```mermaid
graph TD
    Developer([👨‍💻 Developer / CLI]) --> PreFlight[🛡️ Agent 6: OWASP Pre-Flight Sanitizer & Redactor]
    PreFlight --> RouterNode[🔀 Hybrid Model Router & Token Budget Manager]

    subgraph LLM_Backend ["🤖 Hybrid Intelligence Layer"]
        Claude[🧠 Claude 3.5 Sonnet]
        Gemini[💎 Gemini 2.0 / 1.5 Pro]
        DeepSeek[⚡ DeepSeek V3 / R1]
        Ollama[🦙 Local Ollama Engine: qwen2.5-coder:14b]
        BudgetTracker[(📊 Token Budget & Quota Ledger)]
        
        Claude -.->|Quota Reached / 429 / Offline| Ollama
        Gemini -.->|Quota Reached / 429 / Offline| Ollama
        DeepSeek -.->|Quota Reached / 429 / Offline| Ollama
        
        Claude --> BudgetTracker
        Gemini --> BudgetTracker
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
| **1** | **🎯 Lead Architect & Planner** | Cognitive | Claude / Gemini / DeepSeek | Decomposes feature into Clean Architecture layers, identifies existing shared classes via Graphify, and maps `expect`/`actual` bridges. |
| **2** | **🧠 Core Domain Specialist** | Cognitive | Claude / Gemini / `qwen2.5-coder:14b` | Generates pure Kotlin shared logic in `commonMain` (Ktor 3.x, Room KMP/SQLDelight, Coroutines `StateFlow`). |
| **3** | **🎨 Compose UI Specialist** | Cognitive | Claude / Gemini / `qwen2.5-coder:14b` | Implements adaptive Material 3 UI screens and Compose Multiplatform **Resources API** (`Res.string.*`, `Res.drawable.*`). |
| **4** | **📱 Native Bridge Specialist** | Cognitive | Claude / Gemini / `qwen2.5-coder:14b` | Implements `expect` declarations in `commonMain` and platform `actual` code (Android KeyStore, iOS Keychain / `SKIE`, Desktop, Wasm). |
| **5** | **🩺 Diagnostic QA Agent** | Cognitive | Claude / Gemini / `qwen2.5-coder:14b` | Analyzes Kotlin 2.x compiler error logs, matches episodic memory fix recipes, and dispatches targeted diffs. |
| **6** | **🛡️ OWASP Security Guardrail** | Guardian | Deterministic Python / AST | Pre-flight prompt sanitizer, secret redactor, Mobile Top 10 compliance checker, and dependency verification. |
| **7** | **📂 Worktree & File Sandbox** | Guardian | Git Worktree / Pathlib | Provisions `.worktrees/<task-id>`, confines file writes to sandbox, and manages atomic commits and merges. |
| **8** | **⚙️ Gradle Build Runner** | Guardian | Subprocess / Gradle Daemon | Executes isolated `./gradlew check` and extracts structured `CompilerDiagnostic` error logs. |
| **9** | **🖼️ Headless UI Verifier** | Guardian | Compose Desktop Rule / Skiko | Renders and validates `@Preview` composables using headless desktop test harnesses before merge. |

---

## 📚 Production Reference Blueprints (`examples/`)

Explore fully functional reference architecture patterns inside the `examples/` directory:

1. **[Biometric Authentication (`expect`/`actual`)](examples/biometric_auth/)**: Full cross-platform implementation using `BiometricPrompt` on Android and Apple's `LocalAuthentication` (`LAContext`) on iOS.
2. **[OWASP Mobile M1 Secure Storage](examples/secure_storage/)**: Hardware-backed credential encryption using **Android KeyStore** (`EncryptedSharedPreferences`) and **iOS Keychain Services**.
3. **[Offline-First Ktor 3.x + Room KMP](examples/offline_first_networking/)**: Resilient offline sync pattern with reactive Kotlin Coroutines `StateFlow`.

---

## 🚀 Developer Commands (`Makefile` & CLI)

```bash
# 1. Setup & Installation
make install

# 2. Run Pre-Flight Health Check
make health

# 3. Scaffold a Full KMP Starter Project
make init

# 4. Run Automated Test Suite
make test

# 5. Launch Interactive Terminal UI Dashboard
make tui

# 6. Run via Docker Compose (Multi-Agent + Ollama Mesh)
make docker-up
```

---

## 🧪 Testing & CI

Continuous Integration is automatically run on every push and PR via GitHub Actions across **Python 3.9, 3.10, 3.11, 3.12** on **Ubuntu & macOS**.

To run locally:
```bash
python3 -m unittest discover tests
```

---

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.
