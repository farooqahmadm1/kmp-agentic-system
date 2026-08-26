---
name: kmp-testing-mocking
description: Multiplatform unit testing with kotlin.test, Turbine, and Mockative.
triggers:
  - "test"
  - "unit test"
  - "mock"
---

# KMP Testing Standards:
1. Write cross-platform unit tests in `composeApp/src/commonTest/kotlin/...` using `kotlin.test`.
2. Test Kotlin Coroutines Flows with `app.cash.turbine:turbine` using `flow.test { ... }`.
3. Use `Mockative` for pure multiplatform mocking (avoid JVM-only Mockito/MockK in `commonTest`).
