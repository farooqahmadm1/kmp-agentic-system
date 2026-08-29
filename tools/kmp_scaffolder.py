import os
from pathlib import Path
from typing import Optional

class KMPProjectScaffolder:
    """Scaffolds a production-ready, fully runnable Kotlin 2.x + Compose Multiplatform project."""

    @classmethod
    def scaffold(cls, root_dir: str = ".", app_name: str = "ComposeApp", package_name: str = "com.example.kmp"):
        root = Path(root_dir).resolve()
        pkg_path = package_name.replace(".", "/")

        # 1. Directory Tree
        dirs = [
            root / "gradle",
            root / "composeApp",
            root / f"composeApp/src/commonMain/kotlin/{pkg_path}/theme",
            root / f"composeApp/src/commonMain/kotlin/{pkg_path}/domain",
            root / f"composeApp/src/commonMain/kotlin/{pkg_path}/data",
            root / f"composeApp/src/androidMain/kotlin/{pkg_path}",
            root / f"composeApp/src/iosMain/kotlin/{pkg_path}",
            root / f"composeApp/src/desktopMain/kotlin/{pkg_path}",
            root / f"composeApp/src/wasmJsMain/kotlin/{pkg_path}",
            root / f"composeApp/src/commonTest/kotlin/{pkg_path}",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        # 2. gradle/libs.versions.toml
        libs_toml = """[versions]
agp = "8.5.2"
kotlin = "2.0.21"
compose-multiplatform = "1.7.0"
androidx-activityCompose = "1.9.3"
ktor = "3.0.0"
koin = "4.0.0"
coroutines = "1.9.0"
skie = "0.9.0"

[libraries]
androidx-activity-compose = { module = "androidx.activity:activity-compose", version.ref = "androidx-activityCompose" }
kotlinx-coroutines-core = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version.ref = "coroutines" }
ktor-client-core = { module = "io.ktor:ktor-client-core", version.ref = "ktor" }
ktor-client-darwin = { module = "io.ktor:ktor-client-darwin", version.ref = "ktor" }
ktor-client-okhttp = { module = "io.ktor:ktor-client-okhttp", version.ref = "ktor" }
ktor-client-cio = { module = "io.ktor:ktor-client-cio", version.ref = "ktor" }
ktor-client-js = { module = "io.ktor:ktor-client-js", version.ref = "ktor" }
koin-core = { module = "io.insert-koin:koin-core", version.ref = "koin" }
koin-compose = { module = "io.insert-koin:koin-compose", version.ref = "koin" }

[plugins]
androidApplication = { id = "com.android.application", version.ref = "agp" }
androidLibrary = { id = "com.android.library", version.ref = "agp" }
composeMultiplatform = { id = "org.jetbrains.compose", version.ref = "compose-multiplatform" }
composeCompiler = { id = "org.jetbrains.kotlin.plugin.compose", version.ref = "kotlin" }
kotlinMultiplatform = { id = "org.jetbrains.kotlin.multiplatform", version.ref = "kotlin" }
skie = { id = "co.touchlab.skie", version.ref = "skie" }
"""
        (root / "gradle/libs.versions.toml").write_text(libs_toml, encoding="utf-8")

        # 3. settings.gradle.kts
        settings_kts = f"""rootProject.name = "{app_name}"
enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

pluginManagement {{
    repositories {{
        google {{
            mavenContent {{
                includeGroupAndSubgroups("androidx")
                includeGroupAndSubgroups("com.android")
                includeGroupAndSubgroups("com.google")
            }}
        }}
        mavenCentral()
        gradlePluginPortal()
    }}
}}

dependencyResolutionManagement {{
    repositories {{
        google()
        mavenCentral()
    }}
}}

include(":composeApp")
"""
        (root / "settings.gradle.kts").write_text(settings_kts, encoding="utf-8")

        # 4. Root build.gradle.kts
        root_build_kts = """plugins {
    alias(libs.plugins.androidApplication) apply false
    alias(libs.plugins.androidLibrary) apply false
    alias(libs.plugins.composeMultiplatform) apply false
    alias(libs.plugins.composeCompiler) apply false
    alias(libs.plugins.kotlinMultiplatform) apply false
    alias(libs.plugins.skie) apply false
}
"""
        (root / "build.gradle.kts").write_text(root_build_kts, encoding="utf-8")

        # 5. composeApp/build.gradle.kts
        compose_build_kts = f"""import org.jetbrains.compose.desktop.application.dsl.TargetFormat

plugins {{
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeMultiplatform)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.skie)
}}

kotlin {{
    androidTarget()
    
    jvm("desktop")
    
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach {{ iosTarget ->
        iosTarget.binaries.framework {{
            baseName = "ComposeApp"
            isStatic = true
        }}
    }}
    
    @OptIn(org.jetbrains.kotlin.gradle.ExperimentalWasmDsl::class)
    wasmJs {{
        moduleName = "composeApp"
        browser {{
            commonWebpackConfig {{
                outputFileName = "composeApp.js"
            }}
        }}
        binaries.executable()
    }}
    
    sourceSets {{
        commonMain.dependencies {{
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(compose.ui)
            implementation(compose.components.resources)
            implementation(libs.kotlinx.coroutines.core)
            implementation(libs.ktor.client.core)
            implementation(libs.koin.core)
            implementation(libs.koin.compose)
        }}
        androidMain.dependencies {{
            implementation(libs.androidx.activity.compose)
            implementation(libs.ktor.client.okhttp)
        }}
        iosMain.dependencies {{
            implementation(libs.ktor.client.darwin)
        }}
        desktopMain.dependencies {{
            implementation(compose.desktop.currentOs)
            implementation(libs.ktor.client.cio)
        }}
        wasmJsMain.dependencies {{
            implementation(libs.ktor.client.js)
        }}
    }}
}}

android {{
    namespace = "{package_name}"
    compileSdk = 34

    defaultConfig {{
        applicationId = "{package_name}"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }}
}}
"""
        (root / "composeApp/build.gradle.kts").write_text(compose_build_kts, encoding="utf-8")

        # 6. composeApp/src/commonMain/kotlin/.../App.kt
        app_kt = f"""package {package_name}

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun App() {{
    MaterialTheme {{
        var showDetails by remember {{ mutableStateOf(false) }}
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background
        ) {{
            Column(
                modifier = Modifier.fillMaxSize().padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {{
                Text(
                    text = "Welcome to {app_name}!",
                    style = MaterialTheme.typography.headlineMedium
                )
                Spacer(modifier = Modifier.height(16.dp))
                Button(onClick = {{ showDetails = !showDetails }}) {{
                    Text(if (showDetails) "Hide Info" else "Show Platform Info")
                }}
                AnimatedVisibility(showDetails) {{
                    Text(
                        text = "Running on Kotlin Multiplatform 2.x & Compose!",
                        modifier = Modifier.padding(top = 16.dp),
                        style = MaterialTheme.typography.bodyLarge
                    )
                }}
            }}
        }}
    }}
}}
"""
        (root / f"composeApp/src/commonMain/kotlin/{pkg_path}/App.kt").write_text(app_kt, encoding="utf-8")

        # 7. Android MainActivity.kt
        main_activity_kt = f"""package {package_name}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent

class MainActivity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContent {{
            App()
        }}
    }}
}}
"""
        (root / f"composeApp/src/androidMain/kotlin/{pkg_path}/MainActivity.kt").write_text(main_activity_kt, encoding="utf-8")

        # 8. iOS MainViewController.kt
        ios_main_kt = f"""package {package_name}

import androidx.compose.ui.window.ComposeUIViewController

fun MainViewController() = ComposeUIViewController {{ App() }}
"""
        (root / f"composeApp/src/iosMain/kotlin/{pkg_path}/MainViewController.kt").write_text(ios_main_kt, encoding="utf-8")

        # 9. Desktop main.kt
        desktop_main_kt = f"""package {package_name}

import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application

fun main() = application {{
    Window(onCloseRequest = ::exitApplication, title = "{app_name}") {{
        App()
    }}
}}
"""
        (root / f"composeApp/src/desktopMain/kotlin/{pkg_path}/main.kt").write_text(desktop_main_kt, encoding="utf-8")

        # 10. Wasm main.kt
        wasm_main_kt = f"""package {package_name}

import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.window.ComposeViewport
import kotlinx.browser.document

@OptIn(ExperimentalComposeUiApi::class)
fun main() {{
    ComposeViewport(document.body!!) {{
        App()
    }}
}}
"""
        (root / f"composeApp/src/wasmJsMain/kotlin/{pkg_path}/main.kt").write_text(wasm_main_kt, encoding="utf-8")
