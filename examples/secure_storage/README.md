# 🛡️ KMP Blueprint: OWASP Mobile M1 Secure Storage

Enforces hardware-backed encryption for secrets across platforms:
- **`androidMain`**: AES-256-GCM key held in the Android Keystore; SharedPreferences only stores ciphertext (no deprecated `EncryptedSharedPreferences`).
- **`iosMain`**: Apple Keychain Services (`kSecClassGenericPassword`), scoped to one service and `WhenUnlockedThisDeviceOnly`.
