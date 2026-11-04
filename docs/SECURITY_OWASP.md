# 🛡️ OWASP Dual-Layer Security Specification

The KMP Agentic System implements dual-layer security: **Agentic System Guardrails** (OWASP LLM Top 10) and **KMP Application Security** (OWASP Mobile Top 10).

---

## 1. Layer 1: Agentic System Security (OWASP LLM Top 10)

| OWASP Risk | Threat Description | System Mitigation |
| :--- | :--- | :--- |
| **LLM01: Prompt Injection** | User input attempts to override system prompt instructions. | `security/prompt_sanitizer.py` wraps the task description in `<user_task_specification>` delimiters (flagging common override phrases) and existing repo files in `<untrusted_source_file>` blocks, so neither can close its own wrapper. Heuristic, not a guarantee. |
| **LLM02: Sensitive Information Disclosure** | API keys or credentials leaked into prompt payloads. | `security/secret_redactor.py` regex-redacts keys (Anthropic, OpenAI/DeepSeek, Google, AWS, GitHub, Bearer tokens, whole PEM private-key blocks, inline passwords) from every prompt before it reaches any provider. The guardrail also rejects generated files containing them. |
| **LLM06: Excessive Agency** | Agent modifies unauthorized filesystem files or executes destructive commands. | `security/path_sandbox.py` confines reads and writes to the task worktree (blocking `../` and absolute paths), and the guardrail only lets agents write to allowed source sets / Gradle files (`allowed_paths` per project). Files are written only after the guardrail passes. |
| **LLM09: Overreliance / Supply Chain** | Agent generates hallucinated or malicious third-party dependencies (slopsquatting). | `security/dependency_verifier.py` checks planned dependencies against a trusted group-prefix list; anything else is shown as a warning at the plan-approval gate for the human to decide. |
| **LLM10: Model Denial of Service** | Endless self-healing loops burning unbounded tokens or compute. | `max_self_healing_iterations` caps build-fix and guardrail-fix retries (default 5); retries only regenerate the files the errors point at, and `daily_token_limit` caps all cloud usage per day before falling back to local Ollama. |

---

## 2. Layer 2: KMP Application Security (OWASP Mobile Top 10)

These rules are given to the coder agents through `skills/kmp-owasp-security`; only the `commonMain` platform-leak and hardcoded-secret checks are enforced by code. Review the diff at the second approval gate.

| OWASP Mobile Risk | KMP Attack Vector | Agent Guidance |
| :--- | :--- | :--- |
| **M1: Insecure Data Storage** | Plaintext credentials in `SharedPreferences` or `NSUserDefaults`. | Directs agents to hardware-backed encryption: **Android Keystore** (AES-GCM, `AndroidKeyStore`) and **iOS Keychain Services**. |
| **M4: Insufficient Input Validation** | SQL Injection in SQLite or insecure JSON deserialization. | Directs agents to parameterized SQL queries in Room KMP and strict `kotlinx.serialization` configurations. |
| **M5: Insecure Communication** | Cleartext HTTP traffic or unpinned TLS certs. | Directs agents to HTTPS on Ktor Client engines and certificate pinning. |
