"""Plugin-like field registry for the advanced filter engine.

New fields can be added here without touching the core parser or query
builder.  Each entry declares:

  - type:            numeric | text | date | json
  - db_column:       actual column or JSONB path on scoring_snapshots
  - levels:         which hierarchical levels the field is valid for
  - operators:      allowed operators for this field type
  - label:          human-readable label
  - group:          optional grouping for the UI (e.g., "Score", "Name")
"""

from typing import Any

# ---------------------------------------------------------------------------
# Core filterable fields
# ---------------------------------------------------------------------------
FILTERABLE_FIELDS: dict[str, dict[str, Any]] = {
    # Numeric — scores and changes
    "overall_score": {
        "type": "numeric",
        "db_column": "score",
        "levels": ["overall"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Overall Score",
        "group": "Score",
    },
    "overall_change": {
        "type": "numeric",
        "db_column": "score_change",
        "levels": ["overall"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Overall Change",
        "group": "Change",
    },
    "dimension_score": {
        "type": "numeric",
        "db_column": "score",
        "levels": ["dimension"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Dimension Score",
        "group": "Score",
    },
    "dimension_change": {
        "type": "numeric",
        "db_column": "score_change",
        "levels": ["dimension"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Dimension Change",
        "group": "Change",
    },
    "sub_dimension_score": {
        "type": "numeric",
        "db_column": "score",
        "levels": ["sub_dimension"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Sub-Dimension Score",
        "group": "Score",
    },
    "sub_dimension_change": {
        "type": "numeric",
        "db_column": "score_change",
        "levels": ["sub_dimension"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Sub-Dimension Change",
        "group": "Change",
    },
    "aspect_score": {
        "type": "numeric",
        "db_column": "score",
        "levels": ["aspect"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Aspect Score",
        "group": "Score",
    },
    "aspect_change": {
        "type": "numeric",
        "db_column": "score_change",
        "levels": ["aspect"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Aspect Change",
        "group": "Change",
    },
    "sub_aspect_score": {
        "type": "numeric",
        "db_column": "score",
        "levels": ["sub_aspect"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Sub-Aspect Score",
        "group": "Score",
    },
    "sub_aspect_change": {
        "type": "numeric",
        "db_column": "score_change",
        "levels": ["sub_aspect"],
        "operators": ["==", "!=", ">", "<", ">=", "<=", "between", "is_null", "is_not_null"],
        "label": "Sub-Aspect Change",
        "group": "Change",
    },
    # Text — names and categories
    "dimension_name": {
        "type": "text",
        "db_column": "level_name",
        "levels": ["dimension"],
        "operators": ["==", "!=", "contains", "does_not_contain", "starts_with", "ends_with", "in_list", "not_in_list"],
        "label": "Dimension Name",
        "group": "Name",
    },
    "sub_dimension_name": {
        "type": "text",
        "db_column": "level_name",
        "levels": ["sub_dimension"],
        "operators": ["==", "!=", "contains", "does_not_contain", "starts_with", "ends_with", "in_list", "not_in_list"],
        "label": "Sub-Dimension Name",
        "group": "Name",
    },
    "aspect_name": {
        "type": "text",
        "db_column": "level_name",
        "levels": ["aspect"],
        "operators": ["==", "!=", "contains", "does_not_contain", "starts_with", "ends_with", "in_list", "not_in_list"],
        "label": "Aspect Name",
        "group": "Name",
    },
    "sub_aspect_name": {
        "type": "text",
        "db_column": "level_name",
        "levels": ["sub_aspect"],
        "operators": ["==", "!=", "contains", "does_not_contain", "starts_with", "ends_with", "in_list", "not_in_list"],
        "label": "Sub-Aspect Name",
        "group": "Name",
    },
    # Cross-cutting text fields
    "industry": {
        "type": "text",
        "db_column": "industry",
        "levels": ["overall", "dimension", "sub_dimension", "aspect", "sub_aspect"],
        "operators": ["==", "!=", "contains", "does_not_contain", "starts_with", "ends_with", "in_list", "not_in_list"],
        "label": "Industry",
        "group": "Classification",
    },
    "company_id": {
        "type": "text",
        "db_column": "company_id",
        "levels": ["overall", "dimension", "sub_dimension", "aspect", "sub_aspect"],
        "operators": ["==", "!=", "contains", "does_not_contain", "starts_with", "ends_with", "in_list", "not_in_list"],
        "label": "Company ID",
        "group": "Classification",
    },
    # Date
    "timestamp": {
        "type": "date",
        "db_column": "timestamp",
        "levels": ["overall", "dimension", "sub_dimension", "aspect", "sub_aspect"],
        "operators": ["==", "before", "after", "between", "last_n_days", "next_n_days", "year_to_date"],
        "label": "Date",
        "group": "Time",
    },
}


# ---------------------------------------------------------------------------
# Extensible / miscellaneous fields (add new entries here to extend the engine)
# ---------------------------------------------------------------------------
EXTRA_FILTERABLE_FIELDS: dict[str, dict[str, Any]] = {
    "region": {
        "type": "text",
        "db_column": "metadata->>region",
        "levels": ["overall", "dimension", "sub_dimension", "aspect", "sub_aspect"],
        "operators": ["==", "!=", "contains", "does_not_contain", "in_list", "not_in_list"],
        "label": "Region",
        "group": "Misc",
    },
    "department": {
        "type": "text",
        "db_column": "metadata->>department",
        "levels": ["overall", "dimension", "sub_dimension", "aspect", "sub_aspect"],
        "operators": ["==", "!=", "contains", "does_not_contain", "in_list", "not_in_list"],
        "label": "Department",
        "group": "Misc",
    },
    "owner": {
        "type": "text",
        "db_column": "metadata->>owner",
        "levels": ["overall", "dimension", "sub_dimension", "aspect", "sub_aspect"],
        "operators": ["==", "!=", "contains", "does_not_contain", "in_list", "not_in_list"],
        "label": "Owner",
        "group": "Misc",
    },
    "score_status": {
        "type": "text",
        "db_column": "metadata->>score_status",
        "levels": ["overall", "dimension", "sub_dimension", "aspect", "sub_aspect"],
        "operators": ["==", "!=", "in_list", "not_in_list"],
        "label": "Score Status",
        "group": "Misc",
    },
}


def get_field_registry() -> dict[str, dict[str, Any]]:
    """Return the combined field registry (core + extensible)."""
    return {**FILTERABLE_FIELDS, **EXTRA_FILTERABLE_FIELDS}
