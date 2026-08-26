---
name: kmp-build-diagnostics
description: Diagnostic patterns and self-healing recipes for common Kotlin 2.x compiler errors.
triggers:
  - "error"
  - "compiler"
  - "build failure"
---

# KMP Build Diagnostics & Fix Recipes:
1. **Error: Missing actual declaration**:
   - Cause: An `expect` declaration in `commonMain` does not have matching `actual` code in all configured targets.
   - Fix: Generate the missing `actual` in `androidMain`, `iosMain`, `desktopMain`, or `wasmJsMain`.
2. **Error: Leaked platform import in commonMain**:
   - Cause: Found `import android.*` or `import java.io.*` in `commonMain`.
   - Fix: Replace with multiplatform equivalent (`kotlinx.io.*`, `expect/actual` bridge).
