---
name: kmp-gradle-catalog
description: Gradle Kotlin DSL build scripts and libs.versions.toml version catalog management.
triggers:
  - "gradle"
  - "dependencies"
  - "versions.toml"
---

# Gradle & Version Catalog Standards:
1. Always add new dependencies to `gradle/libs.versions.toml` first under `[versions]`, `[libraries]`, and `[plugins]`.
2. Apply `kotlin.applyDefaultHierarchyTemplate()` in `build.gradle.kts`.
3. Configure source set dependencies in `composeApp/build.gradle.kts` using `libs.<alias>`.
