import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from memory import trajectory_log
from memory.session_manager import SessionManager
from memory.graphify_store import GraphifyASTStore
from memory.episodic_store import EpisodicMemoryStore

BROAD_SIG = "Missing actual declaration"
SPECIFIC_SIG = "Missing actual declaration for expect fun getBattery()"
SPECIFIC_ERROR = "e: Missing actual declaration for expect fun getBattery()"


class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.mgr = SessionManager(db_path=str(self.tmp / "sessions.db"))

    def tearDown(self):
        self._tmp.cleanup()

    def test_session_manager(self):
        self.mgr.register_session("task-test-01", "Implement Biometrics", "agent/task-test-01")
        sessions = self.mgr.list_sessions()
        self.assertTrue(any(s["task_id"] == "task-test-01" for s in sessions))

    def test_register_session_defaults_to_active(self):
        self.mgr.register_session("task-a", "Feature A", "agent/task-a")
        (session,) = self.mgr.list_sessions()
        self.assertEqual(session["status"], "ACTIVE")
        self.assertEqual(session["task_description"], "Feature A")
        self.assertEqual(session["branch_name"], "agent/task-a")

    def test_register_session_twice_replaces_row(self):
        self.mgr.register_session("task-a", "Old description", "agent/old")
        self.mgr.register_session("task-a", "New description", "agent/new")
        sessions = self.mgr.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["task_description"], "New description")
        self.assertEqual(sessions[0]["branch_name"], "agent/new")

    def test_update_session_status_only_touches_target(self):
        self.mgr.register_session("task-a", "A", "agent/a")
        self.mgr.register_session("task-b", "B", "agent/b")
        self.mgr.update_session_status("task-a", "COMPLETED")
        statuses = {s["task_id"]: s["status"] for s in self.mgr.list_sessions()}
        self.assertEqual(statuses, {"task-a": "COMPLETED", "task-b": "ACTIVE"})

    def test_list_sessions_empty(self):
        self.assertEqual(self.mgr.list_sessions(), [])

    def test_get_checkpointer_uses_session_db(self):
        checkpointer = self.mgr.get_checkpointer()
        try:
            self.assertIsNotNone(checkpointer)
        finally:
            checkpointer.conn.close()

    def test_export_session_bundle_writes_metadata(self):
        out_dir = self.tmp / "bundles"
        dest = self.mgr.export_session_bundle("task-a", output_dir=str(out_dir))
        self.assertEqual(dest, out_dir / "task-a")
        metadata = json.loads((dest / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["task_id"], "task-a")
        self.assertIn("exported_at", metadata)


class TestEpisodicMemoryStore(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmp.name) / "episodic.db")
        self.store = EpisodicMemoryStore(db_path=self.db_path)

    def tearDown(self):
        self._tmp.cleanup()

    def _rows(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return {
                row["error_signature"]: dict(row)
                for row in conn.execute("SELECT * FROM error_recipes")
            }

    def _record_specific(self):
        self.store.record_solution(
            error_signature=SPECIFIC_SIG,
            category="expect_actual",
            root_cause="Missing iOS actual",
            recipe="Implement actual fun getBattery() in iosMain with UIDevice.current.batteryLevel",
        )

    def test_seeds_golden_recipes(self):
        self.assertEqual(
            set(self._rows()),
            {sig for sig, _, _, _ in EpisodicMemoryStore.SEEDED_RECIPES},
        )

    def test_reopening_does_not_reseed(self):
        self._record_specific()
        EpisodicMemoryStore(db_path=self.db_path)
        self.assertEqual(len(self._rows()), len(EpisodicMemoryStore.SEEDED_RECIPES) + 1)

    def test_episodic_memory(self):
        self._record_specific()
        match = self.store.find_matching_fix(SPECIFIC_ERROR)
        self.assertIsNotNone(match)
        self.assertIn("UIDevice", match["resolution_recipe"])

    def test_most_specific_match_beats_seeded_broad_signature(self):
        # The broad seed was inserted first, so a first-match lookup would return it
        self._record_specific()
        match = self.store.find_matching_fix(SPECIFIC_ERROR)
        self.assertEqual(match["error_signature"], SPECIFIC_SIG)

    def test_most_specific_match_wins_when_inserted_before_broad(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM error_recipes")
        self._record_specific()
        self.store.record_solution(BROAD_SIG, "expect_actual", "Generic", "Add an actual")
        match = self.store.find_matching_fix(SPECIFIC_ERROR)
        self.assertEqual(match["error_signature"], SPECIFIC_SIG)

    def test_broad_signature_still_matches_other_errors(self):
        self._record_specific()
        match = self.store.find_matching_fix("e: Missing actual declaration for class Clock")
        self.assertEqual(match["error_signature"], BROAD_SIG)

    def test_matching_is_case_insensitive(self):
        self._record_specific()
        match = self.store.find_matching_fix(SPECIFIC_ERROR.upper())
        self.assertEqual(match["error_signature"], SPECIFIC_SIG)

        match = self.store.find_matching_fix("E: UNRESOLVED REFERENCE: RES")
        self.assertEqual(match["error_signature"], "Unresolved reference: Res")

    def test_no_match_returns_none(self):
        self.assertIsNone(self.store.find_matching_fix("e: Something entirely unrelated"))
        self.assertIsNone(self.store.find_matching_fix(""))

    def test_hit_count_increments_only_on_returned_row(self):
        self._record_specific()
        before = {sig: row["hit_count"] for sig, row in self._rows().items()}
        self.store.find_matching_fix(SPECIFIC_ERROR)
        after = {sig: row["hit_count"] for sig, row in self._rows().items()}

        self.assertEqual(after[SPECIFIC_SIG], before[SPECIFIC_SIG] + 1)
        # The broad seed also matched the message but was not returned
        self.assertEqual(after[BROAD_SIG], before[BROAD_SIG])
        for sig in before:
            if sig != SPECIFIC_SIG:
                self.assertEqual(after[sig], before[sig], sig)

    def test_no_match_leaves_hit_counts_unchanged(self):
        before = {sig: row["hit_count"] for sig, row in self._rows().items()}
        self.store.find_matching_fix("e: Something entirely unrelated")
        after = {sig: row["hit_count"] for sig, row in self._rows().items()}
        self.assertEqual(after, before)

    def test_record_solution_inserts_new_row(self):
        self._record_specific()
        row = self._rows()[SPECIFIC_SIG]
        self.assertEqual(row["error_category"], "expect_actual")
        self.assertEqual(row["root_cause"], "Missing iOS actual")
        self.assertEqual(row["hit_count"], 1)

    def test_record_solution_upserts_existing_signature(self):
        self._record_specific()
        self.store.record_solution(SPECIFIC_SIG, "expect_actual", "Missing iOS actual", "Use a new recipe")
        rows = self._rows()
        self.assertEqual(len(rows), len(EpisodicMemoryStore.SEEDED_RECIPES) + 1)
        self.assertEqual(rows[SPECIFIC_SIG]["resolution_recipe"], "Use a new recipe")
        self.assertEqual(rows[SPECIFIC_SIG]["hit_count"], 2)

        match = self.store.find_matching_fix(SPECIFIC_ERROR)
        self.assertEqual(match["resolution_recipe"], "Use a new recipe")


class TestGraphifyASTStore(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, rel_path, content):
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_detects_missing_actuals(self):
        self._write("composeApp/src/commonMain/kotlin/Battery.kt", "expect fun getBattery(): Int")
        self._write("composeApp/src/androidMain/kotlin/Battery.kt", "actual fun getBattery(): Int = 1")
        store = GraphifyASTStore(str(self.root))
        store.scan_and_index()
        self.assertEqual(store.get_missing_actuals("ios"), ["getBattery"])
        self.assertEqual(store.get_missing_actuals("android"), [])


class TestTrajectoryLog(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        patcher = mock.patch.object(trajectory_log, "TRAJECTORY_DIR", Path(self._tmp.name) / "trajectory")
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        trajectory_log._current_node.clear()
        self._tmp.cleanup()

    def test_log_and_read_events_round_trip(self):
        trajectory_log.log_event("task-1", "node_start", node="planner")
        trajectory_log.log_event("task-1", "llm_call", tokens=42)
        events = trajectory_log.read_events("task-1")
        self.assertEqual([e["type"] for e in events], ["node_start", "llm_call"])
        self.assertEqual(events[0]["node"], "planner")
        self.assertEqual(events[1]["tokens"], 42)
        self.assertIn("ts", events[0])

    def test_read_events_unknown_task_is_empty(self):
        self.assertEqual(trajectory_log.read_events("missing"), [])

    def test_current_node_is_attributed_until_cleared(self):
        trajectory_log.set_current_node("task-1", "coder")
        trajectory_log.log_event("task-1", "llm_call")
        trajectory_log.log_event("task-1", "override", node="reviewer")
        trajectory_log.set_current_node("task-1", None)
        trajectory_log.log_event("task-1", "after")

        events = trajectory_log.read_events("task-1")
        self.assertEqual(events[0]["node"], "coder")
        self.assertEqual(events[1]["node"], "reviewer")
        self.assertNotIn("node", events[2])

    def test_read_events_skips_corrupt_lines(self):
        trajectory_log.log_event("task-1", "good")
        with open(trajectory_log._path("task-1"), "a", encoding="utf-8") as f:
            f.write("{not json\n")
        trajectory_log.log_event("task-1", "also_good")
        self.assertEqual(
            [e["type"] for e in trajectory_log.read_events("task-1")], ["good", "also_good"]
        )

    def test_task_id_is_sanitized_into_directory(self):
        trajectory_log.log_event("../../evil task", "x")
        path = trajectory_log._path("../../evil task")
        self.assertEqual(path.parent, trajectory_log.TRAJECTORY_DIR)
        self.assertTrue(path.exists())
        self.assertEqual(trajectory_log._path("///"), trajectory_log.TRAJECTORY_DIR / "default.jsonl")

    def test_list_task_ids(self):
        self.assertEqual(trajectory_log.list_task_ids(), [])
        trajectory_log.log_event("task-1", "x")
        trajectory_log.log_event("task-2", "x")
        self.assertEqual(set(trajectory_log.list_task_ids()), {"task-1", "task-2"})

    def test_preview_truncates_long_text(self):
        self.assertEqual(trajectory_log.preview("short"), "short")
        self.assertEqual(trajectory_log.preview(123), "123")
        out = trajectory_log.preview("a" * 10, limit=4)
        self.assertTrue(out.startswith("aaaa\n"))
        self.assertIn("6 more chars", out)


if __name__ == "__main__":
    unittest.main()
