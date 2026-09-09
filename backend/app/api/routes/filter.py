"""Advanced hierarchical filter API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_async_session
from app.schemas.filter_schemas import AdvancedFilterRequest
from app.schemas.schemas import AdvancedFilterResponse, FilterFieldsResponse
from app.services.filter.field_registry import FieldRegistry
from app.services.filter.filter_parser import FilterParseError, parse_filter_tree
from app.services.filter.filter_service import FilterService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["filter"])


@router.post("/advanced", response_model=AdvancedFilterResponse)
async def advanced_filter(
    payload: AdvancedFilterRequest,
    db: AsyncSession = Depends(get_async_session),
) -> AdvancedFilterResponse:
    """
    Apply an advanced hierarchical filter across scoring levels.

    Accepts a nested JSON tree of AND/OR/NOT conditions and returns
    paginated results from the scoring_snapshots table.
    """
    registry = FieldRegistry()
    try:
        parsed = parse_filter_tree(payload.query, registry)
    except (FilterParseError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    service = FilterService()
    try:
        result = await service.execute_filter(
            db=db,
            parsed_root=parsed,
            limit=payload.limit,
            offset=payload.offset,
            sort_by=payload.sort_by or "overall_score",
            sort_dir=payload.sort_dir or "desc",
        )
        return AdvancedFilterResponse(**result)
    except Exception as exc:
        logger.error(f"Advanced filter error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal filter engine error")


@router.get("/fields", response_model=FilterFieldsResponse)
async def list_filterable_fields() -> FilterFieldsResponse:
    """Return the full registry of filterable fields for the UI."""
    registry = FieldRegistry()
    fields = registry.list_all_fields()
    return FilterFieldsResponse(
        status="success",
        fields=fields,
        count=len(fields),
    )
