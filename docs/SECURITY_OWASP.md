# 🛡️ OWASP Dual-Layer Security Specification

The KMP Agentic System implements dual-layer security: **Agentic System Guardrails** (OWASP LLM Top 10) and **KMP Application Security** (OWASP Mobile Top 10).

---

## 1. Layer 1: Agentic System Security (OWASP LLM Top 10)

| OWASP Risk | Threat Description | System Mitigation |
| :--- | :--- | :--- |
| **LLM01: Prompt Injection** | User input attempts to override system prompt instructions. | `security/prompt_sanitizer.py` wraps prompts in strict `<user_task_specification>` XML delimiters and detects override heuristics. |
| **LLM02: Sensitive Information Disclosure** | API keys or credentials leaked into prompt payloads. | `security/secret_redactor.py` executes pre-flight regex and entropy scans to redact keys (`sk-...`, Bearer tokens, private keys) before sending to LLM APIs. |
| **LLM06: Excessive Agency** | Agent modifies unauthorized filesystem files or executes destructive commands. | `security/path_sandbox.py` confines all file operations to `.worktrees/<task-id>` and blocks path traversal attempts (`../`). |
| **LLM09: Overreliance / Supply Chain** | Agent generates hallucinated or malicious third-party dependencies (slopsquatting). | `security/dependency_verifier.py` checks new dependencies against verified Maven Central / Google Maven prefixes. |
| **LLM10: Model Denial of Service** | Endless self-healing loops burning unbounded tokens or compute. | `config.max_self_healing_iterations` enforces a hard cap (default: 5 iterations), terminating failing runs gracefully. |

---

## 2. Layer 2: KMP Application Security (OWASP Mobile Top 10)

| OWASP Mobile Risk | KMP Attack Vector | Agent 6 Guardrail Enforcement |
| :--- | :--- | :--- |
| **M1: Insecure Data Storage** | Plaintext credentials in `SharedPreferences` or `NSUserDefaults`. | Enforces hardware-backed encryption: **Android KeyStore** (`EncryptedSharedPreferences`) and **iOS Keychain Services**. |
| **M4: Insufficient Input Validation** | SQL Injection in SQLite or insecure JSON deserialization. | Enforces parameterized SQL queries in Room KMP and strict `kotlinx.serialization` configurations. |
| **M5: Insecure Communication** | Cleartext HTTP traffic or unpinned TLS certs. | Enforces HTTPS on Ktor Client engines and flags missing certificate pinning configurations. |
