package com.example.kmp.biometrics

import kotlinx.coroutines.suspendCancellableCoroutine
import platform.LocalAuthentication.LAContext
import platform.LocalAuthentication.LAPolicyDeviceOwnerAuthenticationWithBiometrics
import platform.Foundation.NSError
import kotlin.coroutines.resume

actual class BiometricAuth {
    actual suspend fun authenticate(title: String, subtitle: String): BiometricResult =
        suspendCancellableCoroutine { continuation ->
            val context = LAContext()
            val error: NSError? = null

            if (context.canEvaluatePolicy(LAPolicyDeviceOwnerAuthenticationWithBiometrics, error = null)) {
                context.evaluatePolicy(
                    policy = LAPolicyDeviceOwnerAuthenticationWithBiometrics,
                    localizedReason = subtitle
                ) { success, evalError ->
                    if (success) {
                        continuation.resume(BiometricResult.Success)
                    } else {
                        val message = evalError?.localizedDescription ?: "Authentication failed"
                        continuation.resume(BiometricResult.Failure(message))
                    }
                }
            } else {
                continuation.resume(BiometricResult.HardwareUnavailable)
            }
        }
}
