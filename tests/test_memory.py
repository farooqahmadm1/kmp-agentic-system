import unittest
from pathlib import Path
from memory.session_manager import SessionManager
from memory.graphify_store import GraphifyASTStore
from memory.episodic_store import EpisodicMemoryStore

class TestMemory(unittest.TestCase):
    def test_session_manager(self):
        mgr = SessionManager(db_path=".sessions/test_sessions.db")
        mgr.register_session("task-test-01", "Implement Biometrics", "agent/task-test-01")
        sessions = mgr.list_sessions()
        self.assertTrue(any(s["task_id"] == "task-test-01" for s in sessions))

    def test_episodic_memory(self):
        store = EpisodicMemoryStore(db_path=".sessions/test_episodic.db")
        store.record_solution(
            error_signature="Missing actual declaration for expect fun getBattery()",
            category="expect_actual",
            root_cause="Missing iOS actual",
            recipe="Implement actual fun getBattery() in iosMain with UIDevice.current.batteryLevel"
        )
        match = store.find_matching_fix("e: Missing actual declaration for expect fun getBattery()")
        self.assertIsNotNone(match)
        self.assertIn("UIDevice", match["resolution_recipe"])

if __name__ == "__main__":
    unittest.main()
