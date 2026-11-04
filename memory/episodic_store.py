import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

class EpisodicMemoryStore:
    """Tier 4: Evolutionary Memory storing resolved Kotlin/Gradle errors and their working fixes."""

    SEEDED_RECIPES = [
        (
            "Missing actual declaration",
            "expect_actual",
            "Target platform missing actual implementation for commonMain expect contract",
            "Add matching 'actual' class/fun/val in the target source set (e.g., iosMain or androidMain). Ensure default arguments are ONLY on the expect declaration, not actual."
        ),
        (
            "Unresolved reference: android.content.Context",
            "platform_leak",
            "Leaked Android platform import in commonMain",
            "Remove android.* imports from commonMain. Expose an expect/actual platform bridge or inject context via Koin in androidMain."
        ),
        (
            "SKIE link error",
            "ios_native",
            "SKIE plugin unable to export sealed classes or Coroutines Flow to Swift",
            "Ensure 'alias(libs.plugins.skie)' is applied in composeApp/build.gradle.kts and iosTarget framework binary is marked isStatic = true."
        ),
        (
            "Cannot access 'java.io.Serializable'",
            "jvm_leak",
            "Referenced JVM-only Serializable in commonMain",
            "Use @kotlinx.serialization.Serializable with kotlinx.serialization instead of java.io.Serializable."
        ),
        (
            "Ktor Darwin engine not found",
            "networking",
            "Missing platform Ktor client engine for iOS",
            "Add 'libs.ktor.client.darwin' to iosMain.dependencies and 'libs.ktor.client.okhttp' to androidMain.dependencies."
        ),
        (
            "Unresolved reference: Res",
            "compose_resources",
            "Compose Multiplatform Resources API not imported or generated",
            "Ensure 'implementation(compose.components.resources)' is in commonMain.dependencies and import 'package_name.generated.resources.Res'."
        )
    ]

    def __init__(self, db_path: str = ".sessions/episodic_memory.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_signature TEXT UNIQUE,
                    error_category TEXT,
                    root_cause TEXT,
                    resolution_recipe TEXT,
                    hit_count INTEGER DEFAULT 1,
                    source TEXT NOT NULL DEFAULT 'learned'
                )
            """)

            # Migrate databases created before the 'source' column existed. Only rows
            # that still match a seed exactly are known to be seeded; anything else
            # may have been rewritten by record_solution, so treat it as learned.
            columns = {row[1] for row in conn.execute("PRAGMA table_info(error_recipes)")}
            if "source" not in columns:
                conn.execute("ALTER TABLE error_recipes ADD COLUMN source TEXT NOT NULL DEFAULT 'learned'")
                conn.executemany("""
                    UPDATE error_recipes SET source = 'seed'
                    WHERE error_signature = ? AND error_category = ? AND root_cause = ? AND resolution_recipe = ?
                """, self.SEEDED_RECIPES)

            # Sync golden recipes on every init: add missing seeds and refresh seeded
            # rows edited in code, without touching hit_count or learned recipes.
            conn.executemany("""
                INSERT INTO error_recipes (error_signature, error_category, root_cause, resolution_recipe, source)
                VALUES (?, ?, ?, ?, 'seed')
                ON CONFLICT(error_signature) DO UPDATE SET
                    error_category = excluded.error_category,
                    root_cause = excluded.root_cause,
                    resolution_recipe = excluded.resolution_recipe
                WHERE error_recipes.source = 'seed'
            """, self.SEEDED_RECIPES)
            conn.commit()

    def find_matching_fix(self, error_message: str) -> Optional[Dict[str, Any]]:
        """Queries the episodic memory for a known error signature."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM error_recipes")
            rows = cursor.fetchall()
            message = error_message.lower()
            matches = [row for row in rows if row["error_signature"].lower() in message]
            if not matches:
                return None

            # Prefer the most specific (longest) signature so a learned fix like
            # "Missing actual declaration for expect fun getBattery()" beats the
            # broad seeded "Missing actual declaration" recipe.
            best = max(matches, key=lambda row: len(row["error_signature"]))
            conn.execute("UPDATE error_recipes SET hit_count = hit_count + 1 WHERE id = ?", (best["id"],))
            conn.commit()
            return dict(best)

    def record_solution(self, error_signature: str, category: str, root_cause: str, recipe: str):
        """Saves a newly resolved compiler error and its solution recipe to episodic memory."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO error_recipes (error_signature, error_category, root_cause, resolution_recipe)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(error_signature) DO UPDATE SET
                    resolution_recipe = excluded.resolution_recipe,
                    hit_count = hit_count + 1,
                    source = 'learned'
            """, (error_signature, category, root_cause, recipe))
            conn.commit()
