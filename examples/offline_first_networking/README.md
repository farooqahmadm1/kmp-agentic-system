# 🌐 KMP Blueprint: Offline-First Networking (Ktor 3.x + Room KMP)

Demonstrates the clean repository pattern for Kotlin Multiplatform:
- **`commonMain`**: `UserRepository` coordinates between `UserDao` (Room KMP) and `HttpClient` (Ktor 3.x).
- **Graceful Degradation**: If offline, the UI observes cached SQLite records without crashing.
