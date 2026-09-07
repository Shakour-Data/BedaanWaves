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
import urllib.parse
import zipfile
from datetime import date, datetime
from typing import Optional, Union

import requests

logger = logging.getLogger(__name__)

FRED_CSV_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"
HTTP_TIMEOUT = 25
_HTTP_RETRIES = 2
USER_AGENT = (
    "BedaanWaves/2.0 (+https://bedaanwaves.com; free macro data fetcher; "
    "contact@bedaanwaves.com) "
    "FeedFetcher/1.0"
)


def _build_url(series_id: str) -> str:
    params = urllib.parse.urlencode({"id": series_id})
    return f"{FRED_CSV_BASE}?{params}"


def _http_get(url: str) -> Optional[Union[str, bytes]]:
    """GET a URL and return decoded response text or raw bytes (for ZIP), or None on failure.

    Uses requests (not urllib.request) for reliable HTTPS transport.
    Retries once on transient DNS/connection errors.
    Returns raw bytes when the server sends a ZIP archive (Content-Type: application/zip).
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "text/csv, application/zip, */*;q=0.8"}
    for attempt in range(_HTTP_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)  # noqa: S310
            resp.raise_for_status()
            ct = resp.headers.get("Content-Type", "")
            if "zip" in ct or resp.content[:4] == b"PK\x03\x04":
                return resp.content
            return resp.text
        except requests.exceptions.ConnectionError as exc:
            if attempt < _HTTP_RETRIES - 1:
                logger.debug("Transient connection error for %s, retrying: %s", url, exc)
                continue
            logger.warning("HTTP GET failed for %s: %s", url, exc)
            return None
        except requests.exceptions.RequestException as exc:
            logger.warning("HTTP request error for %s: %s", url, exc)
            return None
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Unexpected HTTP error for %s: %s", url, exc)
            return None
    return None


def _fetch_csv(series_id: str) -> Optional[str]:
    """Download the CSV text for a single FRED series id. Returns None on failure."""
    return _http_get(_build_url(series_id))


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
        date_str = (row.get("DATE") or row.get("observation_date") or "").strip()
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
    raw = _http_get(url)
    if raw is None:
        return out

    if isinstance(raw, bytes):
        history_map = _parse_zip(raw, series_ids)
        for sid, points in history_map.items():
            if points:
                out[sid] = points[-1]
        return out

    try:
        reader = csv.DictReader(io.StringIO(raw))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("FRED CSV parse error for %s: %s", ids, exc)
        return out

    for row in reader:
        date_str = (row.get("DATE") or row.get("observation_date") or "").strip()
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
    Handles both plain CSV and ZIP responses from the FRED graph endpoint.
    """
    ids = ",".join(series_ids)
    url = _build_url(ids)
    out: dict[str, list[tuple[date, float]]] = {sid: [] for sid in series_ids}
    raw = _http_get(url)
    if raw is None:
        return out

    if isinstance(raw, bytes):
        return _parse_zip(raw, series_ids)

    try:
        reader = csv.DictReader(io.StringIO(raw))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("FRED CSV parse error for %s: %s", ids, exc)
        return out

    for row in reader:
        date_str = (row.get("DATE") or row.get("observation_date") or "").strip()
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


def _parse_zip(data: bytes, series_ids: list[str]) -> dict[str, list[tuple[date, float]]]:
    """Parse a FRED ZIP response containing monthly.csv, daily.csv, quarterly.csv."""
    out: dict[str, list[tuple[date, float]]] = {sid: [] for sid in series_ids}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                if not name.endswith(".csv"):
                    continue
                try:
                    with zf.open(name) as f:
                        text = f.read().decode("utf-8", errors="replace")
                        reader = csv.DictReader(io.StringIO(text))
                        for row in reader:
                            date_str = (row.get("observation_date") or row.get("DATE") or "").strip()
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
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("FRED ZIP CSV parse error for %s: %s", name, exc)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("FRED ZIP parse error: %s", exc)
    return out


def pct_change(prev: Optional[float], curr: Optional[float]) -> Optional[float]:
    """Trailing percentage change (curr vs prev); None if undeterminable."""
    if prev is None or curr is None or prev == 0:
        return None
    return round((curr / prev - 1.0) * 100.0, 4)
