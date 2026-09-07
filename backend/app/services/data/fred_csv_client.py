"""
FRED (Federal Reserve Economic Data) CSV client.

This client retrieves US macroeconomic indicators from FRED using the public
graph-CSV endpoint:

    https://fred.stlouisfed.org/graph/fredgraph.csv?id=<series_id>[,...]

That endpoint is **free and requires no API key** (it is the same CSV download
the FRED website offers to browsers). No paid subscription is involved.

All network access is wrapped in best-effort error handling: if the host is
unreachable (e.g. an offline/air-gapped deployment), the client returns an
empty result instead of raising, so the rest of the pipeline can fall back to
its bundled snapshot without breaking the scheduler.
"""

from __future__ import annotations

import csv
import io
import logging
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)

FRED_CSV_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"
HTTP_TIMEOUT = 25
USER_AGENT = (
    "BedaanWaves/2.0 (+https://bedaanwaves.com; free macro data fetcher; "
    "contact@bedaanwaves.com) "
    "FeedFetcher/1.0"
)


def _build_url(series_id: str) -> str:
    params = urllib.parse.urlencode({"id": series_id})
    return f"{FRED_CSV_BASE}?{params}"


def _fetch_csv(series_id: str) -> Optional[str]:
    """Download the CSV text for a single FRED series id. Returns None on failure."""
    url = _build_url(series_id)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310 - intentional public endpoint
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.warning("FRED CSV fetch failed for %s: %s", series_id, exc)
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Unexpected FRED fetch error for %s: %s", series_id, exc)
        return None


def _parse_csv(raw: str, series_id: str) -> list[tuple[date, float]]:
    """Parse a FRED graph CSV into (date, value) pairs for the requested series."""
    if not raw:
        return []
    try:
        reader = csv.DictReader(io.StringIO(raw))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("FRED CSV parse error for %s: %s", series_id, exc)
        return []

    points: list[tuple[date, float]] = []
    for row in reader:
        date_str = (row.get("DATE") or "").strip()
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        cell = (row.get(series_id) or "").strip()
        if cell in ("", ".", "NaN", "null"):
            continue
        try:
            value = float(cell)
        except ValueError:
            continue
        points.append((dt, value))
    return points


def fetch_series_history(
    series_id: str, lookback: Optional[int] = None
) -> list[tuple[date, float]]:
    """Return chronological history (oldest first) for a FRED series id."""
    raw = _fetch_csv(series_id)
    points = _parse_csv(raw, series_id)
    if lookback:
        points = points[-lookback:]
    return points


def fetch_latest(series_id: str) -> Optional[tuple[date, float]]:
    """Return (date, value) for the most recent non-null observation."""
    history = fetch_series_history(series_id, lookback=13)
    return history[-1] if history else None


def fetch_latest_map(
    series_ids: list[str],
) -> dict[str, Optional[tuple[date, float]]]:
    """Fetch the latest observation for many series in a single CSV request.

    FRED supports multiple series ids joined by commas in one graph request,
    so we issue one HTTP call for all requested series.
    """
    ids = ",".join(series_ids)
    url = _build_url(ids)
    out: dict[str, Optional[tuple[date, float]]] = {sid: None for sid in series_ids}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.warning("FRED CSV fetch failed for %s: %s", ids, exc)
        return out
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Unexpected FRED fetch error for %s: %s", ids, exc)
        return out

    try:
        reader = csv.DictReader(io.StringIO(raw))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("FRED CSV parse error for %s: %s", ids, exc)
        return out

    for row in reader:
        date_str = (row.get("DATE") or "").strip()
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        for sid in series_ids:
            cell = (row.get(sid) or "").strip()
            if cell in ("", ".", "NaN", "null"):
                continue
            try:
                value = float(cell)
            except ValueError:
                continue
            out[sid] = (dt, value)
    return out


def fetch_history_map(series_ids: list[str]) -> dict[str, list[tuple[date, float]]]:
    """Fetch full (latest-first truncated) history for many series in one request.

    Returns a mapping of series_id -> chronological (oldest-first) points.
    """
    ids = ",".join(series_ids)
    url = _build_url(ids)
    out: dict[str, list[tuple[date, float]]] = {sid: [] for sid in series_ids}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.warning("FRED CSV history fetch failed for %s: %s", ids, exc)
        return out
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Unexpected FRED history fetch error for %s: %s", ids, exc)
        return out

    try:
        reader = csv.DictReader(io.StringIO(raw))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("FRED CSV parse error for %s: %s", ids, exc)
        return out

    for row in reader:
        date_str = (row.get("DATE") or "").strip()
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        for sid in series_ids:
            cell = (row.get(sid) or "").strip()
            if cell in ("", ".", "NaN", "null"):
                continue
            try:
                value = float(cell)
            except ValueError:
                continue
            out[sid].append((dt, value))
    return out


def pct_change(prev: Optional[float], curr: Optional[float]) -> Optional[float]:
    """Trailing percentage change (curr vs prev); None if undeterminable."""
    if prev is None or curr is None or prev == 0:
        return None
    return round((curr / prev - 1.0) * 100.0, 4)
