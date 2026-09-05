"""API integration tests for the advanced filter endpoint."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.filter.filter_service import FilterService
from app.services.filter.filter_parser import parse_filter_tree
from app.services.filter.field_registry import FieldRegistry
from app.schemas.filter_schemas import AdvancedFilterRequest, FilterGroup, FilterCondition, LogicOperator


class FakeRow:
    def __init__(self, **kwargs):
        self.asset = MagicMock()
        self.asset.symbol = kwargs.get("symbol", "TEST")
        self.asset.name = kwargs.get("name", "Test Inc")
        for k, v in kwargs.items():
            if k not in ("symbol", "name"):
                setattr(self, k, v)


def _make_session(rows):
    session = MagicMock()
    result = MagicMock()
    result.scalars = MagicMock(return_value=result)
    result.all = MagicMock(return_value=rows)
    result.mappings = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    session.execute = AsyncMock(return_value=result)
    return session


class TestAdvancedFilterAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

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
            "sort_by": "score",
            "sort_dir": "desc",
        }
        default.update(overrides)
        return default

    @patch("app.api.routes.filter.get_async_session")
    def test_advanced_filter_success(self, mock_get_session):
        rows = [
            FakeRow(id="1", symbol="AAPL", name="Apple", date="2024-01-01", level="overall", level_key="overall", level_name="Overall", score=85.0, score_change=2.5, industry="Technology", company_id="C001", timestamp="2024-01-01T00:00:00"),
        ]
        mock_session = _make_session(rows)
        mock_get_session.return_value = mock_session

        payload = self._build_payload()
        response = self.client.post("/api/v1/filter/advanced", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["results"][0]["symbol"], "AAPL")

    @patch("app.api.routes.filter.get_async_session")
    def test_advanced_filter_invalid_operator(self, mock_get_session):
        mock_session = _make_session([])
        mock_get_session.return_value = mock_session

        payload = self._build_payload()
        payload["query"]["conditions"][0]["operator"] = "invalid_op"
        response = self.client.post("/api/v1/filter/advanced", json=payload)
        self.assertEqual(response.status_code, 400)

    @patch("app.api.routes.filter.get_async_session")
    def test_advanced_filter_empty_results(self, mock_get_session):
        mock_session = _make_session([])
        mock_get_session.return_value = mock_session

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
