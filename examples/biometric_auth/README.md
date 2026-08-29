# 📱 KMP Blueprint: Biometric Authentication

Demonstrates Kotlin 2.x `expect`/`actual` bridge pattern for native biometric hardware:
- **`commonMain`**: `BiometricAuth.kt` defines the common suspend interface and sealed `BiometricResult`.
- **`androidMain`**: `BiometricAuth.android.kt` wraps Jetpack `BiometricPrompt` with coroutines continuation.
- **`iosMain`**: `BiometricAuth.ios.kt` integrates Apple's `LocalAuthentication` framework (`LAContext`).
