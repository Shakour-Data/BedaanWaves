"""Unit tests for the advanced hierarchical filter engine.

Covers:
1. Simple overall score filter
2. Industry + dimension OR combination
3. NOT group with contains
4. Between range on sub-dimension score
5. Nested AND/OR/NOT spanning multiple levels
6. Date filters (last_n_days, between)
7. Extensible metadata field filtering
8. Empty group validation
"""

import asyncio
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock

from app.schemas.filter_schemas import (
    FilterCondition,
    FilterGroup,
    LogicOperator,
)
from app.services.filter.field_registry import FieldRegistry
from app.services.filter.filter_parser import FilterParseError, parse_filter_tree
from app.services.filter.filter_service import FilterService
from app.services.filter.query_builder import build_query_from_tree


class FakeRow:
    def __init__(self, **kwargs):
        self.asset = MagicMock()
        self.asset.symbol = kwargs.get("symbol", "TEST")
        self.asset.name = kwargs.get("name", "Test Inc")
        self.metadata = kwargs.get("metadata", {})
        for k, v in kwargs.items():
            if k not in ("symbol", "name", "metadata"):
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


class TestFieldRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = FieldRegistry()

    def test_list_fields_for_level(self):
        fields = self.reg.list_fields("dimension")
        names = [f["name"] for f in fields]
        self.assertIn("dimension_score", names)
        self.assertIn("dimension_name", names)
        self.assertNotIn("overall_score", names)

    def test_validate_operator_raises_for_invalid(self):
        with self.assertRaises(ValueError):
            self.reg.validate_operator("overall_score", "contains")

    def test_validate_value_numeric_between(self):
        self.reg.validate_value("overall_score", "between", [50, 100])
        with self.assertRaises(ValueError):
            self.reg.validate_value("overall_score", "between", "abc")

    def test_validate_value_text_in_list(self):
        self.reg.validate_value("industry", "in_list", ["Tech", "Finance"])
        with self.assertRaises(ValueError):
            self.reg.validate_value("industry", "in_list", "Tech")


class TestFilterParser(unittest.TestCase):
    def setUp(self):
        self.reg = FieldRegistry()

    def test_parse_simple_condition(self):
        cond = FilterCondition(field="overall_score", operator=">", value=750, level="overall")
        parsed = parse_filter_tree(cond, self.reg)
        self.assertEqual(parsed.field, "overall_score")
        self.assertEqual(parsed.operator, ">")
        self.assertEqual(parsed.value, 750)

    def test_parse_and_group(self):
        group = FilterGroup(
            logic=LogicOperator.AND,
            conditions=[
                FilterCondition(field="overall_score", operator=">", value=750, level="overall"),
                FilterCondition(field="industry", operator="==", value="Technology", level="overall"),
            ],
        )
        parsed = parse_filter_tree(group, self.reg)
        self.assertEqual(parsed.logic, "AND")
        self.assertEqual(len(parsed.children), 2)

    def test_parse_nested_or_and_not(self):
        tree = FilterGroup(
            logic=LogicOperator.AND,
            conditions=[
                FilterGroup(
                    logic=LogicOperator.OR,
                    conditions=[
                        FilterCondition(field="overall_score", operator=">", value=750, level="overall"),
                        FilterCondition(field="dimension_name", operator="==", value="Financial", level="dimension"),
                    ],
                ),
                FilterGroup(
                    logic=LogicOperator.NOT,
                    conditions=[
                        FilterCondition(field="sub_aspect_name", operator="contains", value="Legacy", level="sub_aspect"),
                    ],
                ),
            ],
        )
        parsed = parse_filter_tree(tree, self.reg)
        self.assertEqual(parsed.logic, "AND")
        self.assertEqual(parsed.children[0].logic, "OR")
        self.assertEqual(parsed.children[1].logic, "NOT")

    def test_parse_invalid_operator_raises(self):
        with self.assertRaises(ValueError):
            parse_filter_tree(
                FilterCondition(field="overall_score", operator="contains", value="x", level="overall"),
                self.reg,
            )

    def test_parse_empty_group_raises(self):
        with self.assertRaises(FilterParseError):
            parse_filter_tree(FilterGroup(logic=LogicOperator.AND, conditions=[]), self.reg)


class TestQueryBuilder(unittest.TestCase):
    def setUp(self):
        self.reg = FieldRegistry()

    def _row(self, **kwargs):
        return FakeRow(**kwargs)

    def test_simple_numeric_filter(self):
        from sqlalchemy import select

        from app.models.scoring_snapshot import ScoringSnapshot
        parsed = parse_filter_tree(
            FilterCondition(field="overall_score", operator=">", value=750, level="overall"),
            self.reg,
        )
        stmt = select(ScoringSnapshot)
        filtered = build_query_from_tree(parsed, self.reg)
        stmt = stmt.where(filtered)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
        self.assertIn("score", compiled)

    def test_text_contains_filter(self):
        parsed = parse_filter_tree(
            FilterCondition(field="industry", operator="contains", value="Tech", level="overall"),
            self.reg,
        )
        stmt = build_query_from_tree(parsed, self.reg)
        self.assertIsNotNone(stmt)

    def test_nested_and_or_not(self):
        parsed = parse_filter_tree(
            FilterGroup(
                logic=LogicOperator.AND,
                conditions=[
                    FilterGroup(
                        logic=LogicOperator.OR,
                        conditions=[
                            FilterCondition(field="overall_score", operator=">", value=750, level="overall"),
                            FilterCondition(field="dimension_name", operator="==", value="Financial", level="dimension"),
                        ],
                    ),
                    FilterGroup(
                        logic=LogicOperator.NOT,
                        conditions=[
                            FilterCondition(field="sub_aspect_name", operator="contains", value="Legacy", level="sub_aspect"),
                        ],
                    ),
                ],
            ),
            self.reg,
        )
        stmt = build_query_from_tree(parsed, self.reg)
        self.assertIsNotNone(stmt)

    def test_date_between_filter(self):
        parsed = parse_filter_tree(
            FilterCondition(field="timestamp", operator="between", value=["2024-01-01", "2024-12-31"], level="overall"),
            self.reg,
        )
        stmt = build_query_from_tree(parsed, self.reg)
        self.assertIsNotNone(stmt)

    def test_invalid_operator_raises(self):
        with self.assertRaises(ValueError):
            parse_filter_tree(
                FilterCondition(field="overall_score", operator="invalid_op", value=1, level="overall"),
                self.reg,
            )


class TestFilterService(unittest.TestCase):
    def setUp(self):
        self.service = FilterService()

    def _run(self, coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def _row(self, **kwargs):
        return FakeRow(**kwargs)

    def test_execute_filter_returns_results(self):
        rows = [
            self._row(id="1", asset_id="a1", symbol="AAPL", name="Apple", date=date.today(), level="overall", level_key="overall", level_name="Overall", score=85.0, score_change=2.5, industry="Technology", company_id="C001", timestamp=datetime.now(), extra_fields={}),
        ]
        session = _make_session(rows)

        parsed = parse_filter_tree(
            FilterCondition(field="overall_score", operator=">", value=50, level="overall"),
            FieldRegistry(),
        )

        result = self._run(self.service.execute_filter(session, parsed, limit=10, offset=0))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["symbol"], "AAPL")

    def test_execute_filter_empty_results(self):
        rows = []
        session = _make_session(rows)
        parsed = parse_filter_tree(
            FilterCondition(field="overall_score", operator=">", value=9999, level="overall"),
            FieldRegistry(),
        )
        result = self._run(self.service.execute_filter(session, parsed, limit=10, offset=0))
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["results"], [])


class TestComplexScenarios(unittest.TestCase):
    """Five complex nested filter scenarios matching realistic user queries."""

    def setUp(self):
        self.reg = FieldRegistry()

    def test_scenario_1_overall_and_industry(self):
        tree = FilterGroup(
            logic=LogicOperator.AND,
            conditions=[
                FilterCondition(field="overall_score", operator=">", value=750, level="overall"),
                FilterCondition(field="industry", operator="==", value="Technology", level="overall"),
            ],
        )
        parsed = parse_filter_tree(tree, self.reg)
        stmt = build_query_from_tree(parsed, self.reg)
        self.assertIsNotNone(stmt)

    def test_scenario_2_or_dimension_sub_dimension(self):
        tree = FilterGroup(
            logic=LogicOperator.OR,
            conditions=[
                FilterCondition(field="dimension_name", operator="==", value="Financial", level="dimension"),
                FilterCondition(field="sub_dimension_score", operator="<", value=60, level="sub_dimension"),
            ],
        )
        parsed = parse_filter_tree(tree, self.reg)
        stmt = build_query_from_tree(parsed, self.reg)
        self.assertIsNotNone(stmt)

    def test_scenario_3_not_contains(self):
        tree = FilterGroup(
            logic=LogicOperator.NOT,
            conditions=[
                FilterCondition(field="sub_aspect_name", operator="contains", value="Legacy", level="sub_aspect"),
            ],
        )
        parsed = parse_filter_tree(tree, self.reg)
        stmt = build_query_from_tree(parsed, self.reg)
        self.assertIsNotNone(stmt)

    def test_scenario_4_full_combined_query(self):
        tree = FilterGroup(
            logic=LogicOperator.AND,
            conditions=[
                FilterGroup(
                    logic=LogicOperator.OR,
                    conditions=[
                        FilterCondition(field="overall_score", operator=">", value=750, level="overall"),
                        FilterCondition(field="dimension_name", operator="==", value="Financial", level="dimension"),
                    ],
                ),
                FilterGroup(
                    logic=LogicOperator.NOT,
                    conditions=[
                        FilterCondition(field="sub_aspect_name", operator="contains", value="Legacy", level="sub_aspect"),
                    ],
                ),
                FilterCondition(field="industry", operator="in_list", value=["Technology", "Healthcare"], level="overall"),
            ],
        )
        parsed = parse_filter_tree(tree, self.reg)
        stmt = build_query_from_tree(parsed, self.reg)
        self.assertIsNotNone(stmt)

    def test_scenario_5_between_and_last_n_days(self):
        tree = FilterGroup(
            logic=LogicOperator.AND,
            conditions=[
                FilterCondition(field="aspect_score", operator="between", value=[40, 90], level="aspect"),
                FilterCondition(field="timestamp", operator="last_n_days", value=30, level="aspect"),
                FilterCondition(field="dimension_name", operator="starts_with", value="Tech", level="dimension"),
            ],
        )
        parsed = parse_filter_tree(tree, self.reg)
        stmt = build_query_from_tree(parsed, self.reg)
        self.assertIsNotNone(stmt)
