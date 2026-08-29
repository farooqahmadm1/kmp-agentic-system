package com.example.kmp.storage

/**
 * OWASP Mobile Top 10 M1 Compliance:
 * Common contract for hardware-backed cryptographic storage of auth tokens and credentials.
 */
expect class SecureStorage {
    fun saveString(key: String, value: String)
    fun getString(key: String): String?
    fun remove(key: String)
    fun clearAll()
}
