package com.example.kmp.storage

import kotlinx.cinterop.*
import platform.CoreFoundation.*
import platform.Foundation.*
import platform.Security.*

/**
 * Stores values as Keychain generic passwords, scoped to this app's [service] and readable only
 * while the device is unlocked, never synced or migrated to another device.
 */
@OptIn(ExperimentalForeignApi::class, BetaInteropApi::class)
actual class SecureStorage(private val service: String = "com.example.kmp.securestorage") {

    actual fun saveString(key: String, value: String) {
        val data = NSString.create(string = value).dataUsingEncoding(NSUTF8StringEncoding) ?: return
        remove(key)
        withQuery(key) { query ->
            query.put(kSecValueData, data)
            CFDictionaryAddValue(query, kSecAttrAccessible, kSecAttrAccessibleWhenUnlockedThisDeviceOnly)
            SecItemAdd(query, null)
        }
    }

    actual fun getString(key: String): String? = withQuery(key) { query ->
        CFDictionaryAddValue(query, kSecReturnData, kCFBooleanTrue)
        CFDictionaryAddValue(query, kSecMatchLimit, kSecMatchLimitOne)
        memScoped {
            val result = alloc<CFTypeRefVar>()
            if (SecItemCopyMatching(query, result.ptr) != errSecSuccess) return@memScoped null
            val data = CFBridgingRelease(result.value) as? NSData ?: return@memScoped null
            NSString.create(data = data, encoding = NSUTF8StringEncoding) as String?
        }
    }

    actual fun remove(key: String) {
        withQuery(key) { query -> SecItemDelete(query) }
    }

    actual fun clearAll() {
        // Only this storage's items (same service), not every generic password the app owns
        withQuery(account = null) { query -> SecItemDelete(query) }
    }

    /** Builds a CF query dictionary (retaining its keys/values) for [account] and releases it after [block]. */
    private fun <T> withQuery(account: String?, block: (CFMutableDictionaryRef?) -> T): T {
        val query = CFDictionaryCreateMutable(
            kCFAllocatorDefault, 0, kCFTypeDictionaryKeyCallBacks.ptr, kCFTypeDictionaryValueCallBacks.ptr
        )
        try {
            CFDictionaryAddValue(query, kSecClass, kSecClassGenericPassword)
            query.put(kSecAttrService, NSString.create(string = service))
            if (account != null) query.put(kSecAttrAccount, NSString.create(string = account))
            return block(query)
        } finally {
            CFRelease(query)
        }
    }

    /** Adds a Foundation object to a CF dictionary; the dictionary holds its own retain. */
    private fun CFMutableDictionaryRef?.put(key: CFStringRef?, value: NSObject) {
        val ref = CFBridgingRetain(value)
        CFDictionaryAddValue(this, key, ref)
        CFRelease(ref)
    }
}
