"""Pydantic schemas for the advanced hierarchical filter API."""

from enum import StrEnum
from typing import Any, Union

from pydantic import BaseModel, Field, field_validator


class LogicOperator(StrEnum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class NumericOperator(StrEnum):
    EQ = "=="
    NE = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class TextOperator(StrEnum):
    EQ = "=="
    NE = "!="
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class DateOperator(StrEnum):
    EQ = "=="
    BEFORE = "before"
    AFTER = "after"
    BETWEEN = "between"
    LAST_N_DAYS = "last_n_days"
    NEXT_N_DAYS = "next_n_days"
    YEAR_TO_DATE = "year_to_date"


class FilterLevel(StrEnum):
    OVERALL = "overall"
    DIMENSION = "dimension"
    SUB_DIMENSION = "sub_dimension"
    ASPECT = "aspect"
    SUB_ASPECT = "sub_aspect"


class FilterCondition(BaseModel):
    """Leaf node in the filter tree."""
    field: str
    operator: str
    value: str | int | float | list[Any] | dict[str, Any] | None = None
    level: FilterLevel
    label: str | None = None


class FilterGroup(BaseModel):
    """Internal node in the filter tree."""
    logic: LogicOperator
    conditions: list[Union["FilterGroup", FilterCondition]]


# Allow forward reference
FilterGroup.model_rebuild()


class AdvancedFilterRequest(BaseModel):
    """Top-level payload for POST /api/v1/filter/advanced."""
    query: FilterGroup
    limit: int = Field(100, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort_by: str | None = "score"
    sort_dir: str | None = Field("desc", pattern="^(asc|desc)$")

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: FilterGroup) -> FilterGroup:
        if not v.conditions:
            raise ValueError("query.conditions must not be empty")
        return v


class AdvancedFilterResponse(BaseModel):
    status: str = "success"
    total: int
    limit: int
    offset: int
    results: list[dict[str, Any]]
    applied_filters: list[dict[str, Any]]
    execution_time_ms: float
