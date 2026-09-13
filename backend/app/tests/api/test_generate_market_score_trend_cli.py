"""Tests for the ``generate_market_score_trend`` CLI helper."""

import importlib.util
import os
import sys
import unittest
from datetime import date, timedelta

BACKEND_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
)
SCRIPT_PATH = os.path.join(BACKEND_DIR, "scripts", "generate_market_score_trend.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("gmst_cli", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestGenerateMarketScoreTrendCLI(unittest.TestCase):
    def setUp(self):
        # Ensure the backend dir is importable so the script can resolve
        # ``app.services...`` once it actually runs.
        if BACKEND_DIR not in sys.path:
            sys.path.insert(0, BACKEND_DIR)
        self._argv = sys.argv
        self.module = _load_module()

    def tearDown(self):
        sys.argv = self._argv

    def _with_args(self, *args):
        sys.argv = ["generate_market_score_trend.py", *args]
        # Reload the module to pick up the new sys.argv for parse-time.
        self.module = _load_module()
        return self.module._parse_args()

    def test_default_is_last_30_days(self):
        today = date.today()
        start, end = self._with_args()
        self.assertEqual(end, today)
        self.assertEqual(start, today - timedelta(days=29))

    def test_backfill_default_30_days(self):
        today = date.today()
        start, end = self._with_args("--backfill")
        self.assertEqual(end, today)
        self.assertEqual(start, today - timedelta(days=29))

    def test_backfill_custom_days(self):
        today = date.today()
        start, end = self._with_args("--backfill", "90")
        self.assertEqual(end, today)
        self.assertEqual(start, today - timedelta(days=89))

    def test_explicit_range(self):
        start, end = self._with_args("2026-01-01", "2026-01-31")
        self.assertEqual(start, date(2026, 1, 1))
        self.assertEqual(end, date(2026, 1, 31))

    def test_single_date_defaults_to_30_day_window(self):
        end = date(2026, 8, 1)
        start, parsed_end = self._with_args("2026-08-01")
        self.assertEqual(parsed_end, end)
        self.assertEqual(start, end - timedelta(days=29))