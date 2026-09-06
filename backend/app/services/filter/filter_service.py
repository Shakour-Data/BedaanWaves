"""Service layer for the advanced hierarchical filter API."""

import logging
import time
from typing import Any

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring_snapshot import ScoringSnapshot, SnapshotLevel
from app.services.filter.field_registry import FieldRegistry
from app.services.filter.filter_parser import ParsedCondition, ParsedGroup
from app.services.filter.query_builder import apply_filter_to_query, get_sort_column

logger = logging.getLogger(__name__)


class FilterService:
    """Coordinates parsing, query building, and result formatting."""

    def __init__(self) -> None:
        self.registry = FieldRegistry()

    async def execute_filter(
        self,
        db: AsyncSession,
        parsed_root: ParsedGroup | ParsedCondition,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "overall_score",
        sort_dir: str = "desc",
    ) -> dict[str, Any]:
        start = time.perf_counter()

        base_query = select(ScoringSnapshot)
        filtered_query = apply_filter_to_query(base_query, parsed_root, self.registry)

        # Count total matches
        count_query = select(func.count()).select_from(filtered_query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Sorting
        sort_col = get_sort_column(sort_by, self.registry)
        sort_expr = desc(sort_col) if sort_dir == "desc" else asc(sort_col)
        paged_query = filtered_query.order_by(sort_expr).limit(limit).offset(offset)

        result = await db.execute(paged_query)
        rows = result.scalars().all()

        elapsed_ms = (time.perf_counter() - start) * 1000

        results = [self._row_to_dict(row) for row in rows]
        applied = self._extract_applied_filters(parsed_root)

        return {
            "status": "success",
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": results,
            "applied_filters": applied,
            "execution_time_ms": round(elapsed_ms, 2),
        }

    def _row_to_dict(self, row: ScoringSnapshot) -> dict[str, Any]:
        def _safe_iso(val):
            if val is None:
                return None
            if isinstance(val, str):
                return val
            return val.isoformat()

        return {
            "id": str(row.id),
            "asset_id": str(row.asset_id),
            "symbol": row.asset.symbol if row.asset else None,
            "name": row.asset.name if row.asset else None,
            "date": _safe_iso(row.date),
            "level": row.level.value if isinstance(row.level, SnapshotLevel) else str(row.level),
            "level_key": row.level_key,
            "level_name": row.level_name,
            "score": float(row.score) if row.score is not None else None,
            "score_change": float(row.score_change) if row.score_change is not None else None,
            "industry": row.industry,
            "company_id": row.company_id,
            "timestamp": _safe_iso(row.timestamp),
            "extra_fields": dict(row.metadata) if hasattr(row, "metadata") and row.metadata else {},
        }

    def _extract_applied_filters(self, root: ParsedGroup | ParsedCondition) -> list[dict[str, Any]]:
        """Flatten the filter tree into a list of chip representations."""
        chips: list[dict[str, Any]] = []

        def walk(node: ParsedGroup | ParsedCondition, path: list[str]) -> None:
            if isinstance(node, ParsedCondition):
                chips.append({
                    "field": node.field,
                    "operator": node.operator,
                    "value": node.value,
                    "level": node.level,
                    "path": " / ".join(path) if path else node.field,
                })
            elif isinstance(node, ParsedGroup):
                for child in node.children:
                    walk(child, path + [node.logic])

        walk(root, [])
        return chips
