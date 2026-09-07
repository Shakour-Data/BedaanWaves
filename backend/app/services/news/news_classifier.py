"""
News Classifier - Hybrid keyword + optional Ollama classification.

Classifies news articles into domains:
- POLITICAL / ECONOMIC / INTERNATIONAL / STOCK_MARKET / INDUSTRY / COMPANY
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class NewsClassifier:
    """
    Hybrid classifier using:
    1. Deterministic keyword matching (fast, no dependencies)
    2. Optional local LLM via Ollama (http://localhost:11434) if enabled
    """

    KEYWORD_RULES: dict[str, dict[str, Any]] = {
        "POLITICAL": {
            "keywords": [
                "congress", "senate", "president", "election", "vote", "bill",
                "regulation", "white house", "parliament", "minister", "sanctions",
                "tariff", "legislation", "democrat", "republican", "governor",
                "mayor", "political", "politics", "policy", "campaign", "ballot",
            ],
            "sub_keywords": {
                "US_POLICY": [
                    "white house", "congress", "senate",
                    "house of representatives", "washington",
                ],
                "GEOPOLITICS": [
                    "sanctions", "tariff", "trade war", "nato",
                    "un security council", "middle east", "iran",
                    "china", "russia", "ukraine", "geopolitical",
                ],
                "ELECTION": [
                    "election", "vote", "ballot", "poll",
                    "presidential", "campaign", "candidate",
                ],
            },
        },
        "ECONOMIC": {
            "keywords": [
                "fed", "interest rate", "inflation", "gdp", "unemployment", "jobs report",
                "fomc", "central bank", "treasury", "yield", "recession", "economy",
                "monetary policy", "fiscal", "cpi", "ppi", "nonfarm", "payroll",
                "consumer price", "pce", "deficit", "debt ceiling", "stimulus",
            ],
            "sub_keywords": {
                "FED_POLICY": ["fed", "fomc", "powell", "interest rate", "monetary policy", "rate hike", "rate cut"],
                "EMPLOYMENT": ["jobs report", "nonfarm payrolls", "unemployment", "hiring", "layoffs", "jobless claims"],
                "INFLATION": ["cpi", "ppi", "inflation", "price index", "cost of living"],
            },
        },
        "INTERNATIONAL": {
            "keywords": [
                "global", "world", "international", "overseas", "export", "import",
                "trade deficit", "currency", "forex", "emerging markets", "developing",
                "bretton", "diplomat", "treaty", "alliance", "summit",
            ],
            "sub_keywords": {
                "EUROPE": ["ecb", "european union", "eu", "uk", "germany", "france", "brexit", "euro"],
                "ASIA": ["china", "japan", "india", "korea", "taiwan", "asean", "philippines", "asia-pacific"],
                "MENA": ["saudi", "uae", "israel", "egypt", "oil", "opec", "iran", "qatar", "middle east"],
                "LATAM": ["brazil", "mexico", "argentina", "chile", "colombia", "latam"],
            },
        },
        "STOCK_MARKET": {
            "keywords": [
                "stock", "equity", "nasdaq", "nyse", "s&p 500", "dow jones", "russell",
                "ipo", "listing", "bull market", "bear market", "correction", "rally",
                "sell-off", "trading", "shares", "index fund", "etf", "dividend",
            ],
            "sub_keywords": {
                "INDEX": ["s&p 500", "dow jones", "nasdaq", "russell", "index"],
                "IPO": ["ipo", "initial public offering", "listing", "debut"],
                "ANALYST": ["upgrade", "downgrade", "price target", "analyst", "rating"],
            },
        },
        "INDUSTRY": {
            "keywords": [
                "sector", "industry", "semiconductor", "pharmaceutical", "biotech",
                "energy", "oil & gas", "technology", "software", "hardware", "automotive",
                "aerospace", "defense", "banking", "retail", "consumer", "healthcare",
                "renewable", "mining", "telecom", "media", "entertainment", "logistics",
                "real estate", "construction",
            ],
            "sub_keywords": {
                "TECH": ["software", "hardware", "semiconductor", "cloud", "cybersecurity", "ai", "artificial intelligence"],
                "HEALTHCARE": ["pharmaceutical", "biotech", "drug", "fda", "clinical trial", "vaccine"],
                "ENERGY": ["oil", "gas", "renewable", "solar", "wind", "opec", "refinery"],
                "FINANCE": ["banking", "investment", "hedge fund", "asset management", "fintech", "payment"],
            },
        },
        "COMPANY": {
            "keywords": [
                "earnings", "revenue", "profit", "loss", "merger", "acquisition", "ceo",
                "cfo", "layoff", "hiring", "product launch", "patent", "lawsuit", "settlement",
                "dividend", "stock split", "buyback", "guidance", "outlook",
            ],
            "sub_keywords": {
                "EARNINGS": ["earnings", "revenue", "eps", "profit", "loss", "guidance", "outlook"],
                "MA": ["merger", "acquisition", "takeover", "buyout", "spin-off"],
                "LEADERSHIP": ["ceo", "cfo", "coo", "cmo", "appointed", "resigned", "board"],
            },
        },
    }

    def __init__(self, use_ollama: bool = False) -> None:
        self.use_ollama = use_ollama and bool(
            os.getenv("NEWS_CLASSIFIER_USE_OLLAMA", "False").lower() == "true"
        )
        self._ollama: Any = None

    async def classify(self, title: str, body: str, default_category: str) -> tuple[str, str]:
        text = f"{title} {body}".lower()

        # Company-specific first (highest specificity)
        for category, rules in self.KEYWORD_RULES.items():
            for keyword in rules["keywords"]:
                if keyword in text:
                    sub = self._match_sub(text, rules.get("sub_keywords", {}))
                    return category, sub or category

        if self.use_ollama:
            try:
                return await self._classify_ollama(title, body)
            except Exception as exc:
                logger.warning("Ollama classification failed: %s", exc)

        return default_category, default_category

    def _match_sub(self, text: str, sub_rules: dict[str, list[str]]) -> str | None:
        for sub, keywords in sub_rules.items():
            if any(k in text for k in keywords):
                return sub
        return None

    async def _classify_ollama(self, title: str, body: str) -> tuple[str, str]:
        if self._ollama is None:
            from app.services.news.ollama_classifier import OllamaClassifier
            self._ollama = OllamaClassifier()
        return await self._ollama.classify(title, body)
