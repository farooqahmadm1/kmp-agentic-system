package com.example.kmp.biometrics

/**
 * Common expect declaration for cross-platform biometric authentication.
 * Follows Kotlin 2.x rules: default parameter values are declared ONLY on the expect declaration.
 */
expect class BiometricAuth {
    suspend fun authenticate(
        title: String = "Biometric Authentication",
        subtitle: String = "Verify your identity to proceed"
    ): BiometricResult
}

sealed interface BiometricResult {
    data object Success : BiometricResult
    data class Failure(val errorMessage: String) : BiometricResult
    data object HardwareUnavailable : BiometricResult
}
