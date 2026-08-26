---
name: kmp-expect-actual
description: Enforces Kotlin 2.x rules for expect/actual multiplatform declarations.
triggers:
  - "expect"
  - "actual"
  - "platform bridge"
---

# Kotlin 2.x Expect/Actual Standards:
1. Default parameter values are permitted ONLY on `expect` declarations, never on `actual`.
2. Visibility modifiers and constructor signatures must match identically between `expect` and `actual`.
3. Target matrix mapping:
   - `composeApp/src/commonMain/kotlin/...` (expect declarations)
   - `composeApp/src/androidMain/kotlin/...` (actual android)
   - `composeApp/src/iosMain/kotlin/...` (actual ios)
   - `composeApp/src/desktopMain/kotlin/...` (actual desktop)
   - `composeApp/src/wasmJsMain/kotlin/...` (actual wasmJs)
