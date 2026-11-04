import sqlite3
import tempfile
import unittest
from pathlib import Path

from memory.episodic_store import EpisodicMemoryStore


class TestEpisodicSeeding(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmp.name) / "episodic.db")

    def tearDown(self):
        self._tmp.cleanup()

    def _row(self, signature):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM error_recipes WHERE error_signature = ?", (signature,)
            ).fetchone()
            return dict(row) if row else None

    def _create_legacy_db(self, seeds):
        """Builds a database with the pre-'source' schema, seeded with `seeds`."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE error_recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_signature TEXT UNIQUE,
                    error_category TEXT,
                    root_cause TEXT,
                    resolution_recipe TEXT,
                    hit_count INTEGER DEFAULT 1
                )
            """)
            conn.executemany("""
                INSERT INTO error_recipes (error_signature, error_category, root_cause, resolution_recipe)
                VALUES (?, ?, ?, ?)
            """, seeds)

    def test_new_seed_appears_in_existing_db(self):
        seeds = EpisodicMemoryStore.SEEDED_RECIPES
        self._create_legacy_db(seeds[:-1])

        EpisodicMemoryStore(db_path=self.db_path)

        new_seed = self._row(seeds[-1][0])
        self.assertIsNotNone(new_seed)
        self.assertEqual(new_seed["source"], "seed")
        self.assertEqual(self._row(seeds[0][0])["source"], "seed")

    def test_hit_count_preserved_across_init(self):
        store = EpisodicMemoryStore(db_path=self.db_path)
        signature = EpisodicMemoryStore.SEEDED_RECIPES[0][0]
        store.find_matching_fix(f"e: {signature} for expect class Foo")
        store.find_matching_fix(f"e: {signature} for expect class Foo")

        EpisodicMemoryStore(db_path=self.db_path)

        self.assertEqual(self._row(signature)["hit_count"], 3)

    def test_seed_edit_refreshes_seeded_row(self):
        sig, cat, cause, _ = EpisodicMemoryStore.SEEDED_RECIPES[0]
        self._create_legacy_db([(sig, cat, cause, "old seeded recipe")])
        EpisodicMemoryStore(db_path=self.db_path)
        # Mismatched legacy content is treated as learned, so it survives the migration.
        self.assertEqual(self._row(sig)["resolution_recipe"], "old seeded recipe")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE error_recipes SET source = 'seed' WHERE error_signature = ?", (sig,))
        EpisodicMemoryStore(db_path=self.db_path)

        self.assertEqual(
            self._row(sig)["resolution_recipe"], EpisodicMemoryStore.SEEDED_RECIPES[0][3]
        )

    def test_user_recorded_recipe_not_overwritten(self):
        sig, cat, cause, _ = EpisodicMemoryStore.SEEDED_RECIPES[1]
        store = EpisodicMemoryStore(db_path=self.db_path)
        store.record_solution(sig, cat, cause, "Inject Context through Koin in androidMain")

        EpisodicMemoryStore(db_path=self.db_path)

        row = self._row(sig)
        self.assertEqual(row["resolution_recipe"], "Inject Context through Koin in androidMain")
        self.assertEqual(row["source"], "learned")


if __name__ == "__main__":
    unittest.main()
