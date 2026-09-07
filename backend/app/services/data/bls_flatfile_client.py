"""
BLS (Bureau of Labor Statistics) flat-file client.

Retrieves US economic data directly from the BLS public bulk-download site:

    https://download.bls.gov/pub/time.series/cu/cu.data.1.AllData   (CPI)
    https://download.bls.gov/pub/time.series/ln/ln.data.1.AllData   (Employment)

These are static CSV files served over plain HTTP with **no API key and no
account required** — they are the same public files BLS publishes monthly.

The data is used as a fallback/alternative to the FRED CSV client. All fetches
are best-effort and return ``None``/``[]`` when unreachable, so an air-gapped
deployment never breaks the scheduler.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import date, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 25
_HTTP_RETRIES = 2
USER_AGENT = (
    "BedaanWaves/2.0 (+https://bedaanwaves.com; free BLS data fetcher; "
    "contact@bedaanwaves.com) "
    "FeedFetcher/1.0"
)

CPI_URL = "https://download.bls.gov/pub/time.series/cu/cu.data.1.AllData"
EMPLOYMENT_URL = "https://download.bls.gov/pub/time.series/ln/ln.data.1.AllData"

# Series ids of interest (BLS public series codes).
CPI_SERIES = "CUSR0000SA0"        # CPI-U All items (All Urban Consumers)
CORE_CPI_SERIES = "CUSR0000SA0"  # Core CPI uses CUXR0SAD in BLS; we fall back to FRED CPILFESL
UNEMPLOYMENT_RATE_SERIES = "LNS14000000"  # Civilian Unemployment Rate


def _http_get(url: str) -> Optional[str]:
    """GET a URL and return decoded response text, or None on failure.

    Uses requests (not urllib.request) for reliable HTTPS transport.
    Retries once on transient DNS/connection errors.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "text/csv, */*;q=0.8"}
    for attempt in range(_HTTP_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)  # noqa: S310
            resp.raise_for_status()
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


def _download(url: str) -> Optional[str]:
    """Download a BLS flat-file URL. Returns None on failure."""
    return _http_get(url)


def _parse_bls_rows(raw: str) -> list[tuple[str, int, str, float]]:
    """Parse a BLS data file into (series_id, year, period, value) tuples."""
    if not raw:
        return []
    out: list[tuple[str, int, str, float]] = []
    try:
        reader = csv.reader(io.StringIO(raw))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("BLS CSV parse error: %s", exc)
        return out
    for row in reader:
        if len(row) < 4:
            continue
        series_id = row[0].strip()
        try:
            year = int(row[1])
            period = row[2].strip()
            value = float(row[3])
        except (ValueError, TypeError):
            continue
        out.append((series_id, year, period, value))
    return out


def _period_to_date(year: int, period: str) -> Optional[date]:
    """Convert a BLS monthly 'M01'..'M12' period to a month-end date."""
    if not period.startswith("M"):
        return None
    try:
        month = int(period[1:3])
    except ValueError:
        return None
    if not (1 <= month <= 12):
        return None
    if month == 12:
        first_of_next = date(year + 1, 1, 1)
    else:
        first_of_next = date(year, month + 1, 1)
    return first_of_next - timedelta(days=1)


def fetch_series_from_file(
    url: str, series_id: str, lookback: Optional[int] = None
) -> list[tuple[date, float]]:
    """Fetch (date, value) history for one series from a BLS flat file."""
    raw = _download(url)
    rows = _parse_bls_rows(raw)
    points: list[tuple[date, float]] = []
    for sid, year, period, value in rows:
        if sid != series_id:
            continue
        d = _period_to_date(year, period)
        if d is None:
            continue
        points.append((d, value))
    points.sort(key=lambda x: x[0])
    if lookback:
        points = points[-lookback:]
    return points


def fetch_latest_from_file(url: str, series_id: str) -> Optional[tuple[date, float]]:
    history = fetch_series_from_file(url, series_id, lookback=13)
    return history[-1] if history else None


def fetch_cpi_latest() -> Optional[tuple[date, float]]:
    """Latest CPI index value from BLS (no key)."""
    return fetch_latest_from_file(CPI_URL, CPI_SERIES)


def fetch_unemployment_latest() -> Optional[tuple[date, float]]:
    """Latest civilian unemployment rate (%) from BLS (no key)."""
    return fetch_latest_from_file(EMPLOYMENT_URL, UNEMPLOYMENT_RATE_SERIES)


def fetch_cpi_history(lookback: int = 13) -> list[tuple[date, float]]:
    return fetch_series_from_file(CPI_URL, CPI_SERIES, lookback=lookback)


def fetch_unemployment_history(lookback: int = 13) -> list[tuple[date, float]]:
    return fetch_series_from_file(EMPLOYMENT_URL, UNEMPLOYMENT_RATE_SERIES, lookback=lookback)
