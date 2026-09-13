"""Canonical v2 hierarchy — single source of truth for scoring keys.

Derives the full hierarchy (dimension → sub-dimension → aspect → sub-aspect)
from ``scoring_engine_v2.METRIC_UNIVERSE`` so that every service and endpoint
reads from the same definition.

The METRIC_UNIVERSE tuples are:
    (dim, sub_dim, aspect, sub_aspect, db_field, lower_is_better)

This module exposes:
  - V2_DIMENSIONS:           tuple of the 6 L1 dimension keys
  - V2_SUB_DIMENSIONS:       tuple of all L2 sub-dimension keys
  - V2_ASPECTS:             tuple of all L3 aspect keys
  - V2_SUB_ASPECTS:        tuple of all L4 sub-aspect keys
  - SUB_DIMENSION_TO_PARENT: {sub_dim_key: dimension}  (replaces the legacy dict)
  - ASPECT_TO_PARENT:       {aspect_key: sub_dimension_key}
  - SUB_ASPECT_TO_PARENT:   {sub_aspect_key: aspect_key}
  - ALL_TREND_KEYS:         {level: (keys...)} — canonical allowlist used by
    every trend endpoint + service so the ``keys`` array in the response is
    always correct regardless of what keys exist in the DB JSONB columns.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from app.services.analysis.scoring_engine_v2 import METRIC_UNIVERSE

# ---------------------------------------------------------------------------
# Level key tuples — derived directly from METRIC_UNIVERSE
# ---------------------------------------------------------------------------
_V2_DIMENSIONS: list[str] = []
_V2_SUB_DIMENSIONS: list[str] = []
_V2_ASPECTS: list[str] = []
_V2_SUB_ASPECTS: list[str] = []

SUB_DIMENSION_TO_PARENT: dict[str, str] = {}
ASPECT_TO_PARENT: dict[str, str] = {}
SUB_ASPECT_TO_PARENT: dict[str, str] = {}

for _dim, _sub, _asp, _sa, _db, _lib in METRIC_UNIVERSE:
    if _dim not in _V2_DIMENSIONS:
        _V2_DIMENSIONS.append(_dim)
    if _sub not in _V2_SUB_DIMENSIONS:
        _V2_SUB_DIMENSIONS.append(_sub)
        SUB_DIMENSION_TO_PARENT[_sub] = _dim
    if _asp not in _V2_ASPECTS:
        _V2_ASPECTS.append(_asp)
        ASPECT_TO_PARENT[_asp] = _sub
    if _sa not in _V2_SUB_ASPECTS:
        _V2_SUB_ASPECTS.append(_sa)
        SUB_ASPECT_TO_PARENT[_sa] = _asp

V2_DIMENSIONS: tuple[str, ...] = tuple(_V2_DIMENSIONS)
V2_SUB_DIMENSIONS: tuple[str, ...] = tuple(_V2_SUB_DIMENSIONS)
V2_ASPECTS: tuple[str, ...] = tuple(_V2_ASPECTS)
V2_SUB_ASPECTS: tuple[str, ...] = tuple(_V2_SUB_ASPECTS)

# Canonical allowlist of trend keys per level — the single source of truth
# that every endpoint should expose in its ``keys`` array.
ALL_TREND_KEYS: dict[str, tuple[str, ...]] = {
    "sub_dimension": V2_SUB_DIMENSIONS,
    "aspect": V2_ASPECTS,
    "sub_aspect": V2_SUB_ASPECTS,
}

# Backward-compatible alias for historical import paths.
DIMENSIONS: tuple[str, ...] = V2_DIMENSIONS


def is_dimension_key(key: str) -> bool:
    """Return True if *key* is a known L1 dimension."""
    return key in V2_DIMENSIONS


def is_sub_dimension_key(key: str) -> bool:
    """Return True if *key* is a known L2 sub-dimension."""
    return key in SUB_DIMENSION_TO_PARENT


def is_aspect_key(key: str) -> bool:
    """Return True if *key* is a known L3 aspect."""
    return key in ASPECT_TO_PARENT


def is_sub_aspect_key(key: str) -> bool:
    """Return True if *key* is a known L4 sub-aspect."""
    return key in SUB_ASPECT_TO_PARENT


def aspect_parent(key: str) -> str | None:
    """Return the sub-dimension parent for an aspect key, or None."""
    return ASPECT_TO_PARENT.get(key)


def sub_aspect_parent(key: str) -> str | None:
    """Return the aspect parent for a sub-aspect key, or None."""
    return SUB_ASPECT_TO_PARENT.get(key)


def resolve_level_for_key(key: str) -> str | None:
    """Return the hierarchy level name for a v2 key, or None if unknown."""
    if is_dimension_key(key):
        return "dimension"
    if is_sub_dimension_key(key):
        return "sub_dimension"
    if is_aspect_key(key):
        return "aspect"
    if is_sub_aspect_key(key):
        return "sub_aspect"
    return None


def tier_scores_with_aliases(
    dimension_scores: dict[str, Any] | None,
    sub_dimension_scores: dict[str, Any] | None,
    aspect_scores: dict[str, Any] | None,
    sub_aspect_scores: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return tier scores dict with both singular + plural aliases.

    The two frontend consumers disagree on key naming:
      - ``dashboard/page.tsx`` reads singular  (dimension, sub_dimension, …)
      - ``stocks/[symbol]/scoring/page.tsx`` reads plural  (dimensions, …)

    Emitting both lets us satisfy both without modifying the frontend.
    """
    return {
        "dimension": dimension_scores or {},
        "sub_dimension": sub_dimension_scores or {},
        "aspect": aspect_scores or {},
        "sub_aspect": sub_aspect_scores or {},
        "dimensions": dimension_scores or {},
        "sub_dimensions": sub_dimension_scores or {},
        "aspects": aspect_scores or {},
        "sub_aspects": sub_aspect_scores or {},
    }
