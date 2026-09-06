"""Field registry and validation helpers for the advanced filter engine."""

from typing import Any

from .config import get_field_registry


class FieldRegistry:
    """Encapsulates field metadata and validation."""

    def __init__(self) -> None:
        self._registry = get_field_registry()

    def get_field(self, name: str) -> dict[str, Any]:
        if name not in self._registry:
            raise KeyError(
                f"Unknown filterable field '{name}'. "
                f"Available fields: {sorted(self._registry.keys())}"
            )
        return self._registry[name]

    def list_fields(self, level: str) -> list[dict[str, Any]]:
        return [
            {**meta, "name": name}
            for name, meta in self._registry.items()
            if level in meta.get("levels", [])
        ]

    def list_all_fields(self) -> list[dict[str, Any]]:
        return [
            {**meta, "name": name}
            for name, meta in self._registry.items()
        ]

    def validate_operator(self, field_name: str, operator: str) -> None:
        field = self.get_field(field_name)
        if operator not in field.get("operators", []):
            raise ValueError(
                f"Operator '{operator}' is not valid for field '{field_name}'. "
                f"Allowed: {field.get('operators', [])}"
            )

    def validate_value(self, field_name: str, operator: str, value: Any) -> None:
        field = self.get_field(field_name)
        field_type = field.get("type")

        if operator in ("is_null", "is_not_null"):
            return

        if field_type == "numeric":
            if operator == "between":
                if not isinstance(value, list) or len(value) != 2:
                    raise ValueError("Value for 'between' must be [min, max]")
                for v in value:
                    if not isinstance(v, (int, float)):
                        raise ValueError("Between values must be numeric")
            else:
                if not isinstance(value, (int, float)):
                    raise ValueError("Numeric value required")
        elif field_type == "text":
            if operator in ("in_list", "not_in_list"):
                if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                    raise ValueError("Value for in_list/not_in_list must be a list of strings")
            else:
                if not isinstance(value, str):
                    raise ValueError("Text value required")
        elif field_type == "date":
            if operator == "between":
                if not isinstance(value, list) or len(value) != 2:
                    raise ValueError("Date between requires [start, end]")
            elif operator in ("last_n_days", "next_n_days"):
                if not isinstance(value, int):
                    raise ValueError("N integer required for last_n_days/next_n_days")
            else:
                if not isinstance(value, str):
                    raise ValueError("Date string required")
