---
name: kmp-native-interop
description: iOS SKIE Swift interop, CocoaPods/SPM, and Android Context management.
triggers:
  - "swift"
  - "skie"
  - "context"
  - "interop"
---

# Native Interop Standards:
1. iOS & Swift Interop:
   - Use `SKIE` for exporting Kotlin Coroutines `Flow` to Swift `AsyncSequence` and sealed classes to Swift enums.
   - For C-interop/CocoaPods, write clean bridge headers.
2. Android Context:
   - Never hold strong static references to `Activity` or `Context`.
   - Access `ApplicationContext` via Dependency Injection (Koin) or a dedicated platform bridge provider.
