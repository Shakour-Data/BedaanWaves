"""Recursive parser for the nested filter condition tree.

Converts the JSON payload into an intermediate representation (IR) that the
query builder can consume safely.
"""

from typing import Union, List, Dict, Any
from app.schemas.filter_schemas import FilterGroup, FilterCondition, LogicOperator
from app.services.filter.field_registry import FieldRegistry


class ParsedCondition:
    """Leaf node in the parsed tree."""

    def __init__(self, field: str, operator: str, value: Any, level: str):
        self.field = field
        self.operator = operator
        self.value = value
        self.level = level

    def __repr__(self) -> str:
        return f"ParsedCondition({self.field} {self.operator} {self.value!r} @ {self.level})"


class ParsedGroup:
    """Internal node in the parsed tree."""

    def __init__(self, logic: str, children: List[Union["ParsedGroup", ParsedCondition]]):
        self.logic = logic.upper()
        self.children = children

    def __repr__(self) -> str:
        return f"ParsedGroup({self.logic}, children={self.children!r})"


class FilterParseError(Exception):
    pass


def parse_filter_tree(node: Union[FilterGroup, Dict[str, Any]], registry: FieldRegistry) -> Union[ParsedGroup, ParsedCondition]:
    """Recursively parse a filter node into the internal IR.

    Accepts either a Pydantic model or a raw dict (useful for tests).
    """
    if isinstance(node, dict):
        if "logic" in node:
            node = FilterGroup(**node)
        else:
            node = FilterCondition(**node)

    if isinstance(node, FilterCondition):
        registry.validate_operator(node.field, node.operator)
        registry.validate_value(node.field, node.operator, node.value)
        return ParsedCondition(
            field=node.field,
            operator=node.operator,
            value=node.value,
            level=node.level.value if hasattr(node.level, "value") else str(node.level),
        )

    if isinstance(node, FilterGroup):
        if not node.conditions:
            raise FilterParseError("Filter group must contain at least one condition")
        children = [parse_filter_tree(child, registry) for child in node.conditions]
        return ParsedGroup(logic=node.logic.value, children=children)

    raise FilterParseError(f"Unsupported filter node type: {type(node)!r}")
