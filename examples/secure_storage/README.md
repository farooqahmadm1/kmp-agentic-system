# 🛡️ KMP Blueprint: OWASP Mobile M1 Secure Storage

Enforces hardware-backed encryption for secrets across platforms:
- **`androidMain`**: Uses Android KeyStore with `EncryptedSharedPreferences` (AES-256 GCM).
- **`iosMain`**: Uses Apple Keychain Services API (`kSecClassGenericPassword`).
