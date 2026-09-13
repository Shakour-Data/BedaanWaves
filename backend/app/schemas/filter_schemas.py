"""Pydantic schemas for the advanced hierarchical filter API."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union, Dict, Any
from datetime import date
from enum import Enum


class LogicOperator(str, Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class NumericOperator(str, Enum):
    EQ = "=="
    NE = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class TextOperator(str, Enum):
    EQ = "=="
    NE = "!="
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class DateOperator(str, Enum):
    EQ = "=="
    BEFORE = "before"
    AFTER = "after"
    BETWEEN = "between"
    LAST_N_DAYS = "last_n_days"
    NEXT_N_DAYS = "next_n_days"
    YEAR_TO_DATE = "year_to_date"


class FilterLevel(str, Enum):
    OVERALL = "overall"
    DIMENSION = "dimension"
    SUB_DIMENSION = "sub_dimension"
    ASPECT = "aspect"
    SUB_ASPECT = "sub_aspect"


class FilterCondition(BaseModel):
    """Leaf node in the filter tree."""
    field: str
    operator: str
    value: Optional[Union[str, int, float, List[Any], Dict[str, Any]]] = None
    level: FilterLevel
    label: Optional[str] = None


class FilterGroup(BaseModel):
    """Internal node in the filter tree."""
    logic: LogicOperator
    conditions: List[Union["FilterGroup", FilterCondition]]


# Allow forward reference
FilterGroup.model_rebuild()


class AdvancedFilterRequest(BaseModel):
    """Top-level payload for POST /api/v1/filter/advanced."""
    query: FilterGroup
    limit: int = Field(100, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort_by: Optional[str] = "score"
    sort_dir: Optional[str] = Field("desc", pattern="^(asc|desc)$")

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
    results: List[Dict[str, Any]]
    applied_filters: List[Dict[str, Any]]
    execution_time_ms: float
