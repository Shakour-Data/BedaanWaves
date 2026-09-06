"""Dynamic SQLAlchemy query builder for parsed filter trees.

Converts the parsed IR into safe, parameterized SQLAlchemy expressions.
Never interpolates raw user input into SQL strings.
"""

from typing import Any, Union, List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy import and_, or_, not_, func, cast, String, Date, DateTime
from sqlalchemy.sql import ClauseElement
from sqlalchemy.orm import Query

from app.models.scoring_snapshot import ScoringSnapshot, SnapshotLevel
from app.services.filter.filter_parser import ParsedGroup, ParsedCondition, FilterParseError


class QueryBuildError(Exception):
    pass


def _coerce_level(level_str: str) -> SnapshotLevel:
    return SnapshotLevel(level_str)


def _apply_numeric_filter(column: Any, operator: str, value: Any) -> ClauseElement:
    if operator == "==":
        return column == value
    if operator == "!=":
        return column != value
    if operator == ">":
        return column > value
    if operator == "<":
        return column < value
    if operator == ">=":
        return column >= value
    if operator == "<=":
        return column <= value
    if operator == "between":
        if not isinstance(value, list) or len(value) != 2:
            raise QueryBuildError("between requires [min, max]")
        return column.between(value[0], value[1])
    if operator == "is_null":
        return column.is_(None)
    if operator == "is_not_null":
        return column.is_not(None)
    raise QueryBuildError(f"Unsupported numeric operator: {operator}")


def _apply_text_filter(column: Any, operator: str, value: Any) -> ClauseElement:
    if operator == "==":
        return column == value
    if operator == "!=":
        return column != value
    if operator == "contains":
        return column.ilike(f"%{value}%")
    if operator == "does_not_contain":
        return ~column.ilike(f"%{value}%")
    if operator == "starts_with":
        return column.ilike(f"{value}%")
    if operator == "ends_with":
        return column.ilike(f"%{value}")
    if operator == "in_list":
        if not isinstance(value, list):
            raise QueryBuildError("in_list requires a list of values")
        return column.in_(value)
    if operator == "not_in_list":
        if not isinstance(value, list):
            raise QueryBuildError("not_in_list requires a list of values")
        return column.notin_(value)
    raise QueryBuildError(f"Unsupported text operator: {operator}")


def _apply_date_filter(column: Any, operator: str, value: Any) -> ClauseElement:
    if operator == "==":
        target = datetime.strptime(value, "%Y-%m-%d").date() if isinstance(value, str) else value
        return cast(column, Date) == target
    if operator == "before":
        target = datetime.strptime(value, "%Y-%m-%d").date() if isinstance(value, str) else value
        return cast(column, Date) < target
    if operator == "after":
        target = datetime.strptime(value, "%Y-%m-%d").date() if isinstance(value, str) else value
        return cast(column, Date) > target
    if operator == "between":
        if not isinstance(value, list) or len(value) != 2:
            raise QueryBuildError("between requires [start, end]")
        start = datetime.strptime(value[0], "%Y-%m-%d").date() if isinstance(value[0], str) else value[0]
        end = datetime.strptime(value[1], "%Y-%m-%d").date() if isinstance(value[1], str) else value[1]
        return cast(column, Date).between(start, end)
    if operator == "last_n_days":
        n = int(value)
        target_date = date.today() - timedelta(days=n)
        return cast(column, Date) >= target_date
    if operator == "next_n_days":
        n = int(value)
        target_date = date.today() + timedelta(days=n)
        return cast(column, Date) <= target_date
    if operator == "year_to_date":
        start = date(date.today().year, 1, 1)
        return cast(column, Date).between(start, date.today())
    raise QueryBuildError(f"Unsupported date operator: {operator}")


def _column_for_field(field_name: str, registry) -> Any:
    from app.models.scoring_snapshot import ScoringSnapshot
    from app.services.filter.config import FILTERABLE_FIELDS, EXTRA_FILTERABLE_FIELDS

    all_fields = {**FILTERABLE_FIELDS, **EXTRA_FILTERABLE_FIELDS}
    meta = all_fields.get(field_name)
    if not meta:
        raise QueryBuildError(f"Unknown field: {field_name}")

    db_col = meta["db_column"]
    field_type = meta["type"]

    model = ScoringSnapshot
    if db_col == "score":
        return model.score
    if db_col == "score_change":
        return model.score_change
    if db_col == "level_name":
        return model.level_name
    if db_col == "industry":
        return model.industry
    if db_col == "company_id":
        return model.company_id
    if db_col == "timestamp":
        return model.timestamp
    if db_col == "date":
        return model.date
    if db_col.startswith("metadata->>"):
        path = db_col.split("->>")[1]
        return model.metadata[path].astext

    raise QueryBuildError(f"Cannot map field '{field_name}' with db_column '{db_col}'")


def _apply_filter(column: Any, operator: str, value: Any, field_type: str) -> ClauseElement:
    if field_type == "numeric":
        return _apply_numeric_filter(column, operator, value)
    if field_type == "text":
        return _apply_text_filter(column, operator, value)
    if field_type == "date":
        return _apply_date_filter(column, operator, value)
    raise QueryBuildError(f"Unsupported field type: {field_type}")


def build_query_from_tree(
    root: Union[ParsedGroup, ParsedCondition],
    registry,
) -> ClauseElement:
    """Recursively convert the parsed filter tree into a SQLAlchemy clause."""
    from app.services.filter.config import FILTERABLE_FIELDS, EXTRA_FILTERABLE_FIELDS

    if isinstance(root, ParsedCondition):
        column = _column_for_field(root.field, registry)
        meta = {**FILTERABLE_FIELDS, **EXTRA_FILTERABLE_FIELDS}.get(root.field, {})
        return _apply_filter(column, root.operator, root.value, meta.get("type", "text"))

    # Group node
    clauses = [build_query_from_tree(child, registry) for child in root.children]
    logic = root.logic

    if logic == "AND":
        return and_(*clauses)
    if logic == "OR":
        return or_(*clauses)
    if logic == "NOT":
        if len(clauses) != 1:
            raise QueryBuildError("NOT group must contain exactly one child")
        return not_(clauses[0])

    raise QueryBuildError(f"Unsupported logic operator: {logic}")


def apply_filter_to_query(
    query: Any,
    root: Union[ParsedGroup, ParsedCondition],
    registry,
) -> Any:
    """Apply a parsed filter tree to an existing SQLAlchemy query."""
    clause = build_query_from_tree(root, registry)
    return query.where(clause)


def get_sort_column(sort_by: str, registry):
    try:
        return _column_for_field(sort_by, registry)
    except QueryBuildError:
        from app.models.scoring_snapshot import ScoringSnapshot
        return ScoringSnapshot.score
