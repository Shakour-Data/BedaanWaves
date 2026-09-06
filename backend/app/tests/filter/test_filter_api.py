"""API integration tests for the advanced filter endpoint."""

import unittest
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.filter import get_async_session as real_get_session
from app.api.routes.filter import router as filter_router


class FakeRow:
    def __init__(self, **kwargs):
        self.asset = MagicMock()
        self.asset.symbol = kwargs.get("symbol", "TEST")
        self.asset.name = kwargs.get("name", "Test Inc")
        self.extra_fields = kwargs.get("extra_fields", {})
        for k, v in kwargs.items():
            if k not in ("symbol", "name", "extra_fields"):
                setattr(self, k, v)


def _make_session(rows):
    session = MagicMock()

    rows_result = MagicMock()
    rows_result.scalars.return_value = rows_result
    rows_result.all.return_value = rows

    count_result = MagicMock()
    count_result.scalar.return_value = len(rows)

    async def execute_mock(query, *args, **kwargs):
        stmt_str = str(query)
        if "count()" in stmt_str or "count(*)" in stmt_str:
            return count_result
        return rows_result

    session.execute = execute_mock
    return session


def _create_test_app():
    _app = FastAPI()
    _app.include_router(filter_router, prefix="/api/v1/filter", tags=["filter"])
    return _app


class TestAdvancedFilterAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(_create_test_app())

    def _build_payload(self, **overrides):
        default = {
            "query": {
                "logic": "AND",
                "conditions": [
                    {"field": "overall_score", "operator": ">", "value": 500, "level": "overall"},
                    {"field": "industry", "operator": "==", "value": "Technology", "level": "overall"},
                ],
            },
            "limit": 10,
            "offset": 0,
            "sort_by": "overall_score",
            "sort_dir": "desc",
        }
        default.update(overrides)
        return default

    def test_advanced_filter_success(self):
        rows = [
            FakeRow(id="1", asset_id="a1", symbol="AAPL", name="Apple", date="2024-01-01", level="overall", level_key="overall", level_name="Overall", score=85.0, score_change=2.5, industry="Technology", company_id="C001", timestamp="2024-01-01T00:00:00"),
        ]
        mock_session = _make_session(rows)
        self.client.app.dependency_overrides[real_get_session] = lambda: mock_session

        payload = self._build_payload()
        response = self.client.post("/api/v1/filter/advanced", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["results"][0]["symbol"], "AAPL")

    def test_advanced_filter_invalid_operator(self):
        mock_session = _make_session([])
        self.client.app.dependency_overrides[real_get_session] = lambda: mock_session

        payload = self._build_payload()
        payload["query"]["conditions"][0]["operator"] = "invalid_op"
        response = self.client.post("/api/v1/filter/advanced", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_advanced_filter_empty_results(self):
        mock_session = _make_session([])
        self.client.app.dependency_overrides[real_get_session] = lambda: mock_session

        payload = self._build_payload()
        payload["query"]["conditions"][0]["value"] = 9999
        response = self.client.post("/api/v1/filter/advanced", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["results"], [])

    def test_list_fields_endpoint(self):
        response = self.client.get("/api/v1/filter/fields")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("fields", data)
        self.assertTrue(len(data["fields"]) > 0)
