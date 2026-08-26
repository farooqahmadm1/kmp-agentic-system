---
name: compose-multiplatform-ui
description: Best practices for declarative Compose Multiplatform UI and Compose Resources API.
triggers:
  - "ui"
  - "screen"
  - "composable"
  - "material3"
---

# Compose Multiplatform UI Standards:
1. Use Material 3 (`androidx.compose.material3.*`) components for all screens.
2. Use the official Compose Multiplatform Resources API:
   - `stringResource(Res.string.some_text)`
   - `painterResource(Res.drawable.some_icon)`
3. Handle adaptive window sizes using `BoxWithConstraints` or `calculateWindowSizeClass()`.
4. Ensure ViewModels expose state via Kotlin Coroutines `StateFlow` and collect using `collectAsStateMultiplatform()` or `collectAsState()`.
