"""
Continuous News Ingestion Service.

Long-lived background service that continuously polls registered news sources
at their configured intervals and pushes new items to DB + SSE.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import aiohttp
from defusedxml.ElementTree import fromstring as safe_fromstring
from sqlalchemy import select

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import Asset, News, NewsSource
from app.services.core.base_service import BaseService
from app.services.news.news_classifier import NewsClassifier
from app.services.news.source_registry import DEFAULT_NEWS_SOURCES

logger = logging.getLogger(__name__)

# Default user agent for HTTP requests
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# In-memory dedup set (complements DB unique constraint on News.url)
_MAX_SEEN_URLS = 100_000


def _jitter(center: float, pct: float = 0.15) -> float:
    if center <= 0:
        return 0.0
    spread = center * pct
    return center + (spread * (1.0 if (hash(uuid.uuid4().hex) & 1) else -1.0) * 0.3)


@dataclass
class _SourceState:
    name: str
    interval: float
    consecutive_failures: int = 0
    last_success: datetime | None = None
    last_error: str | None = None


class ContinuousNewsIngestionService(BaseService):
    """
    Continuously polls registered news sources and ingests new items.

    Unlike SchedulerService batch jobs, this service maintains persistent
    per-source poll loops and emits events immediately upon detection.
    """

    def __init__(
        self,
        settings: Any | None = None,
        news_service: Any | None = None,
        orchestrator: Any | None = None,
        on_new_item: Callable[[dict[str, Any]], Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        super().__init__("ContinuousNewsIngestionService")
        self._settings = settings or get_settings()
        self._news_service = news_service
        self._orch = orchestrator
        self._on_new_item = on_new_item
        self._source_loops: dict[str, asyncio.Task] = {}
        self._stop_event = asyncio.Event()
        self._seen_urls: set[str] = set()
        self._source_states: dict[str, _SourceState] = {}
        self._classifier = NewsClassifier()
        self._session: aiohttp.ClientSession | None = None

    async def initialize(self) -> None:
        """Start all source poll loops."""
        self._session = aiohttp.ClientSession(
            headers={"User-Agent": _USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=30),
        )
        sources = await self._load_active_sources()
        for source in sources:
            state = _SourceState(name=source["name"], interval=source["interval"])
            self._source_states[source["name"]] = state
            task = asyncio.create_task(self._source_loop(source))
            self._source_loops[source["name"]] = task
        self.logger.info(f"Started {len(self._source_loops)} news source loops")

    async def shutdown(self) -> None:
        """Cancel all loops and close HTTP session."""
        self._stop_event.set()
        for task in self._source_loops.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*self._source_loops.values(), return_exceptions=True)
        self._source_loops.clear()
        if self._session is not None:
            await self._session.close()
        self.logger.info("ContinuousNewsIngestionService shutdown complete")

    async def subscribe(self) -> asyncio.Queue:
        """Return a queue that receives new news items as they arrive."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=4096)
        self._on_new_item = lambda item: queue.put_nowait(item) if not queue.full() else None
        return queue

    # ------------------------------------------------------------------ #
    # Source management
    # ------------------------------------------------------------------ #

    async def _load_active_sources(self) -> list[dict[str, Any]]:
        """Load enabled sources from DB, fallback to default registry."""
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(NewsSource).where(NewsSource.enabled)
                )
                sources = result.scalars().all()
                if sources:
                    return [
                        {
                            "name": s.name,
                            "url": s.url,
                            "type": s.source_type,
                            "category": s.category,
                            "region": s.region,
                            "interval": s.interval_seconds,
                            "max_concurrent": s.max_concurrent_requests,
                        }
                        for s in sources
                    ]
        except Exception as exc:
            logger.warning("Failed to load sources from DB: %s", exc)

        return DEFAULT_NEWS_SOURCES

    async def _record_source_success(self, name: str) -> None:
        state = self._source_states.get(name)
        if state:
            state.consecutive_failures = 0
            state.last_success = datetime.now(UTC)
            state.last_error = None
        try:
            async with async_session_maker() as session:
                source = await session.get(NewsSource, name)
                if source:
                    source.last_success_at = datetime.now(UTC)
                    source.success_count_24h += 1
                    await session.commit()
        except Exception:
            pass

    async def _record_source_failure(self, name: str, error: str) -> None:
        state = self._source_states.get(name)
        if state:
            state.consecutive_failures += 1
            state.last_error = error
        try:
            async with async_session_maker() as session:
                source = await session.get(NewsSource, name)
                if source:
                    source.last_error_at = datetime.now(UTC)
                    source.last_error_message = error[:1000]
                    source.failure_count_24h += 1
                    await session.commit()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Poll loops
    # ------------------------------------------------------------------ #

    async def _source_loop(self, source: dict[str, Any]) -> None:
        base_interval = float(source["interval"])
        while not self._stop_event.is_set():
            try:
                await self._fetch_and_process(source)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Source %s error: %s", source["name"], exc)
                await self._record_source_failure(source["name"], str(exc))

            state = self._source_states.get(source["name"])
            interval = base_interval
            if state and state.consecutive_failures > 3:
                interval = min(base_interval * 5, 3600)

            await asyncio.sleep(_jitter(interval, pct=0.1))

    async def _fetch_and_process(self, source: dict[str, Any]) -> None:
        raw_items = await self._fetch_source(source)
        if not raw_items:
            await self._record_source_success(source["name"])
            return

        processed = 0
        async with async_session_maker() as session:
            for item in raw_items:
                url = (item.get("url") or "").strip()
                if not url:
                    continue
                if url in self._seen_urls:
                    continue

                existing = await session.execute(
                    select(News.id).where(News.url == url)
                )
                if existing.scalar_one_or_none():
                    self._seen_urls.add(url)
                    continue

                title = item.get("title", "") or ""
                body = item.get("body") or ""
                category, sub_category = await self._classifier.classify(
                    title, body, source["category"]
                )
                asset_id = await self._link_asset(title, body)
                priority = self._determine_priority(title, category)

                news = News(
                    source=source["name"],
                    title=title[:512],
                    body=body[:4000] if body else None,
                    url=url,
                    category=category,
                    sub_category=sub_category,
                    region=source.get("region", "GLOBAL"),
                    priority=priority,
                    language=item.get("language", "en"),
                    asset_id=asset_id,
                    published_at=item.get("published_at"),
                    is_market_moving=self._is_market_moving(title),
                )
                session.add(news)
                self._seen_urls.add(url)
                processed += 1

                if self._on_new_item is not None:
                    payload = {
                        "news_id": str(news.id),
                        "title": news.title,
                        "body": news.body,
                        "source": news.source,
                        "url": news.url,
                        "category": news.category,
                        "sub_category": news.sub_category,
                        "region": news.region,
                        "priority": news.priority,
                        "language": news.language,
                        "asset_id": str(news.asset_id) if news.asset_id else None,
                        "published_at": news.published_at.isoformat() if news.published_at else None,
                        "is_market_moving": news.is_market_moving,
                    }
                    try:
                        self._on_new_item(payload)
                    except Exception:
                        pass

                # Keep in-memory dedup bounded
                if len(self._seen_urls) > _MAX_SEEN_URLS:
                    self._seen_urls = set(list(self._seen_urls)[-(_MAX_SEEN_URLS // 2):])

            await session.commit()

        if processed > 0:
            await self._record_source_success(source["name"])
        logger.debug("%s: processed %d new items", source["name"], processed)

    # ------------------------------------------------------------------ #
    # Fetching
    # ------------------------------------------------------------------ #

    async def _fetch_source(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        url = source["url"]
        source_type = source.get("type", "RSS").upper()

        if source_type == "RSS":
            return await self._fetch_rss(url, source)
        if source_type == "JSON":
            return await self._fetch_json(url, source)
        return []

    async def _fetch_rss(self, url: str, source: dict[str, Any]) -> list[dict[str, Any]]:
        text = await self._get_text(url)
        if not text:
            return []
        try:
            root = safe_fromstring(text)
        except Exception as exc:
            logger.debug("RSS parse failed for %s: %s", source["name"], exc)
            return []

        items: list[dict[str, Any]] = []
        for item_elem in root.iter("item"):
            title = self._elem_text(item_elem, "title")
            link = self._elem_text(item_elem, "link")
            pub_date = self._elem_text(item_elem, "pubDate")
            description = self._elem_text(item_elem, "description")
            if not title:
                continue
            published_at = self._parse_date(pub_date) or datetime.now(UTC)
            body = self._strip_html(description) if description else title
            items.append({
                "title": title,
                "url": link or "",
                "published_at": published_at.replace(tzinfo=None),
                "body": body[:4000],
                "language": "en",
            })
        return items

    async def _fetch_json(self, url: str, source: dict[str, Any]) -> list[dict[str, Any]]:
        data = await self._get_json(url)
        if not isinstance(data, dict):
            return []

        items: list[dict[str, Any]] = []
        if source["name"] == "stocktwits":
            for msg in data.get("messages", [])[:20]:
                body = msg.get("body", "")
                created = msg.get("created_at")
                published_at = (
                    datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if created else datetime.now(UTC)
                )
                msg_id = msg.get("id", "")
                link = f"https://stocktwits.com/message/{msg_id}" if msg_id else ""
                items.append({
                    "title": body[:200],
                    "url": link,
                    "published_at": published_at.replace(tzinfo=None),
                    "body": body,
                    "language": "en",
                })
        elif source["name"] in ("reddit_wallstreetbets", "reddit_stocks"):
            children = (
                data.get("data", {}).get("children", [])
                if isinstance(data, dict) else []
            )
            for child in children:
                post = child.get("data", {}) if isinstance(child, dict) else {}
                title = post.get("title", "")
                permalink = post.get("permalink", "")
                link = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")
                created = post.get("created_utc")
                published_at = (
                    datetime.fromtimestamp(created, tz=UTC) if created else datetime.now(UTC)
                )
                self_comment = post.get("selftext", "")
                body = self_comment[:500] if self_comment else title
                items.append({
                    "title": title,
                    "url": link,
                    "published_at": published_at.replace(tzinfo=None),
                    "body": body,
                    "language": "en",
                })
        return items

    async def _get_text(self, url: str) -> str | None:
        for attempt in range(2):
            try:
                async with self._session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    if response.status == 404:
                        return None
            except Exception as exc:
                logger.debug("GET %s failed (attempt %d): %s", url, attempt + 1, exc)
                await asyncio.sleep(min(2 ** attempt, 5))
        return None

    async def _get_json(self, url: str) -> Any:
        for attempt in range(2):
            try:
                async with self._session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    if response.status in (404, 403):
                        return None
            except Exception as exc:
                logger.debug("GET JSON %s failed (attempt %d): %s", url, attempt + 1, exc)
                await asyncio.sleep(min(2 ** attempt, 5))
        return None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    async def _link_asset(self, title: str, body: str) -> uuid.UUID | None:
        """Try to link news to an asset by symbol mention."""
        text = f"{title} {body}".upper()
        async with async_session_maker() as session:
            result = await session.execute(
                select(Asset.id, Asset.symbol).where(Asset.active, Asset.market == "NASDAQ")
            )
            for asset_id, symbol in result.all():
                if symbol in text:
                    return asset_id
        return None

    @staticmethod
    def _determine_priority(title: str, category: str) -> str:
        text = title.lower()
        high_indicators = ["breaking", "urgent", "just in", "alert", "flash", "exclusive"]
        critical_indicators = ["market crash", "black monday", "circuit breaker", "halt", "halted"]
        if any(k in text for k in critical_indicators):
            return "CRITICAL"
        if any(k in text for k in high_indicators):
            return "HIGH"
        if category in ("ECONOMIC", "STOCK_MARKET"):
            return "HIGH"
        return "NORMAL"

    @staticmethod
    def _is_market_moving(title: str) -> bool:
        keywords = [
            "fed", "fomc", "interest rate", "inflation", "jobs report", "gdp",
            "earnings", "revenue", "guidance", "merger", "acquisition", "ipo",
            "dividend", "stock split", "buyback", "ceo", "cfo", "layoff",
            "sanctions", "tariff", "trade war", "opec", "oil price",
        ]
        text = title.lower()
        return any(k in text for k in keywords)

    @staticmethod
    def _elem_text(parent: Any, tag: str) -> str:
        elem = parent.find(tag)
        return (elem.text or "").strip() if elem is not None else ""

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        if not date_str:
            return None
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except ValueError:
                continue
        try:
            ts = float(date_str)
            return datetime.fromtimestamp(ts, tz=UTC)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _strip_html(html: str) -> str:
        if not html:
            return ""
        text = html.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
        import re
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()
