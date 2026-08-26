---
name: kmp-owasp-security
description: Enforces OWASP Mobile Top 10 security standards in Kotlin Multiplatform code.
triggers:
  - "storage"
  - "auth"
  - "network"
  - "credentials"
  - "tokens"
---

# OWASP Mobile Security Rules for KMP:
1. **M1 Secure Storage**:
   - NEVER save authentication tokens, user credentials, or encryption keys in plain `SharedPreferences` (Android) or `NSUserDefaults` (iOS).
   - Enforce `expect`/`actual` bridges targeting **Android KeyStore** (`EncryptedSharedPreferences`) and **iOS Keychain Services** (`SecItemAdd` / `SecItemCopyMatching`).
2. **M4 Injection & Serialization**:
   - Use parameterized SQL queries with Room KMP or SQLDelight (never string concatenation in queries).
   - Use safe `kotlinx.serialization` configurations (`ignoreUnknownKeys = true`).
3. **M5 Secure Communication**:
   - Enforce HTTPS across all Ktor Client engines.
   - Configure certificate pinning via `CertificatePinner` where necessary.
