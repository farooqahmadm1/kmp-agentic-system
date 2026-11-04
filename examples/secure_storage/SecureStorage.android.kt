package com.example.kmp.storage

import android.content.Context
import android.content.SharedPreferences
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Values are encrypted with an AES-256-GCM key that lives in the Android Keystore (hardware-backed
 * where the device supports it) and never leaves it; SharedPreferences only ever holds ciphertext.
 *
 * Uses the platform Keystore directly instead of androidx.security:security-crypto
 * (`EncryptedSharedPreferences`), which is deprecated.
 */
actual class SecureStorage(context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("kmp_secure_prefs", Context.MODE_PRIVATE)

    private val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }

    private fun secretKey(): SecretKey {
        (keyStore.getEntry(KEY_ALIAS, null) as? KeyStore.SecretKeyEntry)?.let { return it.secretKey }
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build()
        )
        return generator.generateKey()
    }

    actual fun saveString(key: String, value: String) {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey()) // Keystore picks a fresh random IV
        // Bind the ciphertext to its key name so a value can't be swapped in under another key
        cipher.updateAAD(key.encodeToByteArray())
        val sealed = cipher.iv + cipher.doFinal(value.encodeToByteArray())
        prefs.edit().putString(key, Base64.encodeToString(sealed, Base64.NO_WRAP)).apply()
    }

    actual fun getString(key: String): String? {
        val sealed = prefs.getString(key, null)?.let { Base64.decode(it, Base64.NO_WRAP) } ?: return null
        if (sealed.size <= IV_BYTES) return null
        return try {
            val cipher = Cipher.getInstance(TRANSFORMATION)
            cipher.init(Cipher.DECRYPT_MODE, secretKey(), GCMParameterSpec(TAG_BITS, sealed, 0, IV_BYTES))
            cipher.updateAAD(key.encodeToByteArray())
            cipher.doFinal(sealed, IV_BYTES, sealed.size - IV_BYTES).decodeToString()
        } catch (e: java.security.GeneralSecurityException) {
            null // tampered value, or the key was invalidated (e.g. app data restored to a new device)
        }
    }

    actual fun remove(key: String) {
        prefs.edit().remove(key).apply()
    }

    actual fun clearAll() {
        prefs.edit().clear().apply()
    }

    private companion object {
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val KEY_ALIAS = "kmp_secure_storage_key"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val IV_BYTES = 12
        const val TAG_BITS = 128
    }
}
