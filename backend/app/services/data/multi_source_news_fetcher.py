"""
Multi-Source News Fetcher - Aggregates news from 10 free sources without API keys.

Sources:
1. Google News RSS (symbol-specific search)
2. Yahoo Finance RSS (symbol headlines)
3. CNBC RSS (market news + symbol search)
4. Reuters RSS (business/finance news)
5. MarketWatch RSS (market top stories)
6. SEC EDGAR (US company filings)
7. Reddit JSON (retail sentiment from relevant subreddits)
8. Stocktwits (trader chatter per symbol)
9. Nasdaq RSS (Nasdaq market news)
10. Benzinga RSS (financial news)
"""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from defusedxml.ElementTree import fromstring as safe_fromstring
from datetime import timezone, datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlencode

import aiohttp

from app.models.models import News
from app.services.core.base_service import DataService

logger = logging.getLogger(__name__)

# Default user agent for requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# RSS namespace map
RSS_NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


class MultiSourceNewsFetcher(DataService):
    """
    Aggregates financial news from 10 free sources without requiring API keys.
    """

    def __init__(
        self,
        service_name: str = "MultiSourceNewsFetcher",
        timeout: int = 15,
        max_retries: int = 2,
    ):
        super().__init__(service_name)
        self.timeout = timeout
        self.max_retries = max_retries

    async def initialize(self) -> None:
        self.logger.info("MultiSourceNewsFetcher initialized")

    async def shutdown(self) -> None:
        self.logger.info("MultiSourceNewsFetcher shutdown")

    async def fetch_news_for_symbol(
        self,
        symbol: str,
        days: int = 7,
        asset_id: Optional[str] = None,
        language: str = "en",
    ) -> List[News]:
        """
        Fetch news for a specific symbol from all available sources.

        Args:
            symbol: Stock ticker symbol (e.g., AAPL, MSFT)
            days: Lookback period in days
            asset_id: Optional asset UUID for DB insertion
            language: Language code

        Returns:
            List of News objects deduplicated by URL
        """
        symbol = symbol.upper().strip()
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
        seen_urls: set = set()
        news_items: List[News] = []

        # Source 1: Google News RSS (symbol search)
        google_news = await self._fetch_google_news_rss(symbol)
        for item in google_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Source 2: Yahoo Finance RSS
        yahoo_news = await self._fetch_yahoo_finance_rss(symbol)
        for item in yahoo_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Source 3: CNBC RSS
        cnbc_news = await self._fetch_cnbc_rss(symbol)
        for item in cnbc_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Source 4: Reuters RSS
        reuters_news = await self._fetch_reuters_rss(symbol)
        for item in reuters_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Source 5: MarketWatch RSS
        mw_news = await self._fetch_marketwatch_rss()
        for item in mw_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Source 6: SEC EDGAR (US companies only)
        sec_news = await self._fetch_sec_edgar(symbol)
        for item in sec_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Source 7: Reddit JSON
        reddit_news = await self._fetch_reddit_json(symbol)
        for item in reddit_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Source 8: Stocktwits
        st_news = await self._fetch_stocktwits(symbol)
        for item in st_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Source 9: Nasdaq RSS
        nasdaq_news = await self._fetch_nasdaq_rss()
        for item in nasdaq_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Source 10: Benzinga RSS
        benzinga_news = await self._fetch_benzinga_rss()
        for item in benzinga_news:
            if item.url and item.url not in seen_urls:
                if item.published_at and item.published_at.timestamp() >= cutoff:
                    seen_urls.add(item.url)
                    news_items.append(item)

        # Attach asset_id and language
        for item in news_items:
            item.asset_id = asset_id
            item.language = language
            item.fetched_at = datetime.utcnow()

        self.logger.info(
            f"Fetched {len(news_items)} news items for {symbol} from {len(set(n.source for n in news_items))} sources"
        )
        return news_items

    async def fetch_market_news(self, limit: int = 20) -> List[News]:
        """
        Fetch general market news from general RSS sources.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of News objects
        """
        seen_urls: set = set()
        news_items: List[News] = []

        sources = [
            self._fetch_marketwatch_rss(),
            self._fetch_reuters_rss("stock"),
            self._fetch_nasdaq_rss(),
            self._fetch_benzinga_rss(),
            self._fetch_cnbc_rss("market"),
        ]

        results = await asyncio.gather(*sources, return_exceptions=True)
        for source_result in results:
            if isinstance(source_result, Exception):
                continue
            for item in source_result:
                if item.url and item.url not in seen_urls:
                    seen_urls.add(item.url)
                    item.language = "en"
                    item.fetched_at = datetime.utcnow()
                    news_items.append(item)
                    if len(news_items) >= limit * 3:
                        break
            if len(news_items) >= limit * 3:
                break

        news_items.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        return news_items[:limit]

    # ------------------------------------------------------------------
    # Source 1: Google News RSS
    # ------------------------------------------------------------------
    async def _fetch_google_news_rss(self, symbol: str) -> List[News]:
        url = f"https://news.google.com/rss/search?q={quote_plus(symbol)}+stock&hl=en-US&gl=US&ceid=US:en"
        return await self._fetch_rss(url, "Google News", symbol)

    # ------------------------------------------------------------------
    # Source 2: Yahoo Finance RSS
    # ------------------------------------------------------------------
    async def _fetch_yahoo_finance_rss(self, symbol: str) -> List[News]:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
        return await self._fetch_rss(url, "Yahoo Finance", symbol)

    # ------------------------------------------------------------------
    # Source 3: CNBC RSS
    # ------------------------------------------------------------------
    async def _fetch_cnbc_rss(self, symbol: str) -> List[News]:
        url = (
            "https://search.cnbc.com/rs/search/combinedcms/view.xml"
            f"?partid=119005645&tagId=119005645&query={quote_plus(symbol)}"
        )
        return await self._fetch_rss(url, "CNBC", symbol)

    # ------------------------------------------------------------------
    # Source 4: Reuters RSS
    # ------------------------------------------------------------------
    async def _fetch_reuters_rss(self, symbol: str) -> List[News]:
        url = "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"
        items = await self._fetch_rss(url, "Reuters", symbol)
        for item in items:
            item.source = "Reuters"
        return items

    # ------------------------------------------------------------------
    # Source 5: MarketWatch RSS
    # ------------------------------------------------------------------
    async def _fetch_marketwatch_rss(self) -> List[News]:
        url = "https://feeds.content.dowjones.io/public/rss/mw_topstories"
        items = await self._fetch_rss(url, "MarketWatch", "market")
        for item in items:
            item.source = "MarketWatch"
        return items

    # ------------------------------------------------------------------
    # Source 6: SEC EDGAR
    # ------------------------------------------------------------------
    async def _fetch_sec_edgar(self, symbol: str) -> List[News]:
        url = (
            "https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={symbol}&type=10-K&dateb=&owner=include&count=40&output=atom"
        )
        return await self._fetch_rss(url, "SEC EDGAR", symbol)

    # ------------------------------------------------------------------
    # Source 7: Reddit JSON
    # ------------------------------------------------------------------
    async def _fetch_reddit_json(self, symbol: str) -> List[News]:
        subreddits = ["wallstreetbets", "stocks", "investing", "StockMarket"]
        tasks = []
        for sub in subreddits:
            url = (
                f"https://www.reddit.com/r/{sub}/search.json"
                f"?q={quote_plus(symbol)}&restrict_sr=1&sort=new&limit=10"
            )
            tasks.append(self._fetch_reddit_json_one(url, sub, symbol))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        items: List[News] = []
        for r in results:
            if isinstance(r, list):
                items.extend(r)
        return items

    async def _fetch_reddit_json_one(self, url: str, subreddit: str, symbol: str) -> List[News]:
        items: List[News] = []
        try:
            data = await self._get_json(url, headers={"User-Agent": USER_AGENT})
            children = (
                data.get("data", {}).get("children", [])
                if isinstance(data, dict)
                else []
            )
            for child in children:
                post = child.get("data", {}) if isinstance(child, dict) else {}
                title = post.get("title", "")
                permalink = post.get("permalink", "")
                link = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")
                created = post.get("created_utc")
                published_at = datetime.fromtimestamp(created, tz=timezone.utc) if created else datetime.utcnow()
                self_comment = post.get("selftext", "")
                body = self_comment[:500] if self_comment else title

                items.append(
                    News(
                        source=f"Reddit/{subreddit}",
                        title=title,
                        body=body,
                        url=link,
                        published_at=published_at.replace(tzinfo=None),
                        language="en",
                    )
                )
        except Exception as e:
            self.logger.debug(f"Reddit fetch failed for r/{subreddit}: {e}")
        return items

    # ------------------------------------------------------------------
    # Source 8: Stocktwits
    # ------------------------------------------------------------------
    async def _fetch_stocktwits(self, symbol: str) -> List[News]:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
        items: List[News] = []
        try:
            data = await self._get_json(url, headers={"User-Agent": USER_AGENT})
            messages = (
                data.get("messages", [])
                if isinstance(data, dict)
                else []
            )
            for msg in messages[:20]:
                body = msg.get("body", "")
                created = msg.get("created_at")
                published_at = datetime.fromisoformat(created.replace("Z", "+00:00")) if created else datetime.utcnow()
                msg_id = msg.get("id", "")
                link = f"https://stocktwits.com/message/{msg_id}" if msg_id else ""
                items.append(
                    News(
                        source="Stocktwits",
                        title=body[:200],
                        body=body,
                        url=link,
                        published_at=published_at.replace(tzinfo=None),
                        language="en",
                    )
                )
        except Exception as e:
            self.logger.debug(f"Stocktwits fetch failed for {symbol}: {e}")
        return items

    # ------------------------------------------------------------------
    # Source 9: Nasdaq RSS
    # ------------------------------------------------------------------
    async def _fetch_nasdaq_rss(self) -> List[News]:
        url = "https://www.nasdaq.com/feed/rssoutbound"
        items = await self._fetch_rss(url, "Nasdaq", "market")
        for item in items:
            item.source = "Nasdaq"
        return items

    # ------------------------------------------------------------------
    # Source 10: Benzinga RSS
    # ------------------------------------------------------------------
    async def _fetch_benzinga_rss(self) -> List[News]:
        url = "https://www.benzinga.com/feed"
        items = await self._fetch_rss(url, "Benzinga", "market")
        for item in items:
            item.source = "Benzinga"
        return items

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    async def _fetch_rss(self, url: str, source_name: str, symbol: str) -> List[News]:
        items: List[News] = []
        try:
            text = await self._get_text(url)
            if not text:
                return items
            root = safe_fromstring(text)
            for item_elem in root.iter("item"):
                title = self._elem_text(item_elem, "title")
                link = self._elem_text(item_elem, "link")
                pub_date = self._elem_text(item_elem, "pubDate")
                description = self._elem_text(item_elem, "description")

                published_at = self._parse_date(pub_date)
                if not published_at:
                    published_at = datetime.now(timezone.utc)

                body = self._strip_html(description) if description else (title or "")
                if not title:
                    continue

                items.append(
                    News(
                        source=source_name,
                        title=title,
                        body=body[:2000],
                        url=link or "",
                        published_at=published_at.replace(tzinfo=None),
                        language="en",
                    )
                )
        except Exception as e:
            self.logger.debug(f"RSS fetch failed for {source_name} ({symbol}): {e}")
        return items

    async def _get_text(self, url: str) -> Optional[str]:
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        headers={"User-Agent": USER_AGENT},
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        if response.status == 200:
                            return await response.text()
                        if response.status == 404:
                            return None
            except Exception as e:
                self.logger.debug(f"GET {url} failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(min(2 ** attempt, 5))
        return None

    async def _get_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    req_headers = {"User-Agent": USER_AGENT}
                    if headers:
                        req_headers.update(headers)
                    async with session.get(
                        url,
                        headers=req_headers,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        if response.status in (404, 403):
                            return None
            except Exception as e:
                self.logger.debug(f"GET JSON {url} failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(min(2 ** attempt, 5))
        return None

    @staticmethod
    def _elem_text(parent: ET.Element, tag: str) -> str:
        elem = parent.find(tag)
        return (elem.text or "").strip() if elem is not None else ""

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
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
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        try:
            ts = float(date_str)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _strip_html(html: str) -> str:
        if not html:
            return ""
        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&quot;", '"', text)
        text = re.sub(r"&#\d+;", "", text)
        return text.strip()
