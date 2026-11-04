import unittest
import tempfile
from pathlib import Path
from models.json_repair import JSONRepair
from models.token_budget import TokenBudgetManager

class TestModels(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_json_repair_markdown(self):
        raw_markdown = '```json\n{"feature_name": "auth", "target_platforms": ["android", "ios"]}\n```'
        parsed = JSONRepair.parse_or_repair(raw_markdown)
        self.assertEqual(parsed["feature_name"], "auth")
        self.assertEqual(len(parsed["target_platforms"]), 2)

    def test_json_repair_trailing_commas(self):
        raw_trailing = '{"dependencies": ["io.ktor:ktor-client-core:3.0.0",],}'
        parsed = JSONRepair.parse_or_repair(raw_trailing)
        self.assertEqual(len(parsed["dependencies"]), 1)

    def test_token_budget_manager(self):
        mgr = TokenBudgetManager(db_path=str(self.tmp / "budget.db"), daily_token_limit=1000)
        mgr.record_usage("test-task", "deepseek_cloud", "deepseek-chat", 200, 300)
        stats = mgr.get_today_usage()
        self.assertEqual(stats["total_tokens_today"], 500)
        self.assertFalse(stats["is_quota_exceeded"])

if __name__ == "__main__":
    unittest.main()
