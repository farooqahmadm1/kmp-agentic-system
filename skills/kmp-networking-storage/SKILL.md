---
name: kmp-networking-storage
description: Ktor 3.x multiplatform client configuration and Room KMP / SQLDelight persistence.
triggers:
  - "ktor"
  - "http"
  - "room"
  - "sqldelight"
---

# KMP Networking & Storage Standards:
1. Ktor 3.x Client Engines:
   - iOS: `Darwin` engine with custom session configuration.
   - Android: `OkHttp` engine.
   - Desktop: `CIO` engine.
   - Wasm/JS: `Js` engine.
2. Serialization: Use `kotlinx.serialization.json.Json { ignoreUnknownKeys = true; isLenient = true }`.
3. Room KMP: Use `Room.databaseBuilder()` configured via `expect`/`actual` platform factories.
