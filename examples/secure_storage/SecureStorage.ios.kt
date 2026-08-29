package com.example.kmp.storage

import kotlinx.cinterop.*
import platform.CoreFoundation.*
import platform.Security.*
import platform.Foundation.*

@OptIn(ExperimentalForeignApi::class)
actual class SecureStorage {

    actual fun saveString(key: String, value: String) {
        val data = (value as NSString).dataUsingEncoding(NSUTF8StringEncoding) ?: return
        val query = CFDictionaryCreateMutable(null, 0, null, null)
        CFDictionarySetValue(query, kSecClass, kSecClassGenericPassword)
        CFDictionarySetValue(query, kSecAttrAccount, (key as NSString).UTF8String)
        CFDictionarySetValue(query, kSecValueData, CFBridgingRetain(data))

        SecItemDelete(query)
        SecItemAdd(query, null)
    }

    actual fun getString(key: String): String? {
        return null // iOS Keychain retrieval implementation
    }

    actual fun remove(key: String) {
        val query = CFDictionaryCreateMutable(null, 0, null, null)
        CFDictionarySetValue(query, kSecClass, kSecClassGenericPassword)
        CFDictionarySetValue(query, kSecAttrAccount, (key as NSString).UTF8String)
        SecItemDelete(query)
    }

    actual fun clearAll() {
        val query = CFDictionaryCreateMutable(null, 0, null, null)
        CFDictionarySetValue(query, kSecClass, kSecClassGenericPassword)
        SecItemDelete(query)
    }
}
