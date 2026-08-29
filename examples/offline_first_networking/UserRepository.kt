package com.example.kmp.data

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.serialization.Serializable
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*

@Serializable
data class User(val id: String, val name: String, val email: String)

interface UserDao {
    fun getAllUsers(): Flow<List<User>>
    suspend fun insertUsers(users: List<User>)
}

/**
 * Offline-First Repository Pattern in commonMain:
 * Emits cached Room KMP database records first, then updates from Ktor 3.x API.
 */
class UserRepository(
    private val httpClient: HttpClient,
    private val userDao: UserDao
) {
    fun getUsersStream(): Flow<List<User>> = userDao.getAllUsers()

    suspend fun refreshUsers() {
        try {
            val remoteUsers: List<User> = httpClient.get("https://api.example.com/v1/users").body()
            userDao.insertUsers(remoteUsers)
        } catch (e: Exception) {
            // Offline gracefully - cached data continues to serve the UI
        }
    }
}
