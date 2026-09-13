"""
Ollama Local LLM Classifier.

Optional local LLM classification via Ollama (no API keys required).
Requires Ollama running on localhost:11434.
"""

from __future__ import annotations

import json
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OllamaClassifier:
    """Local LLM classifier via Ollama."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.NEWS_OLLAMA_URL.rstrip("/")
        self.model = self.settings.NEWS_OLLAMA_MODEL

    async def classify(self, title: str, body: str) -> tuple[str, str]:
        prompt = (
            "Classify this news article into exactly one of these categories:\n"
            "- POLITICAL (government, elections, policy, regulation, sanctions)\n"
            "- ECONOMIC (Fed, inflation, GDP, jobs, central banks, markets)\n"
            "- INTERNATIONAL (global affairs, trade, diplomacy, conflicts)\n"
            "- STOCK_MARKET (equities, indices, IPOs, trading)\n"
            "- INDUSTRY (sectors like tech, healthcare, energy, finance)\n"
            "- COMPANY (corporate earnings, M&A, leadership, products)\n\n"
            "Also provide a sub-category from: US_POLICY, GEOPOLITICS, FED_POLICY, EMPLOYMENT, INFLATION, "
            "EUROPE, ASIA, MENA, LATAM, TECH, HEALTHCARE, ENERGY, FINANCE, EARNINGS, MA, LEADERSHIP\n\n"
            f"Title: {title}\nBody: {body[:500]}\n\n"
            'Respond in JSON: {"category": "...", "sub_category": "..."}'
        )

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                if response.status_code == 200:
                    result = json.loads(response.json()["response"])
                    category = result.get("category", "ECONOMIC")
                    sub_category = result.get("sub_category", category)
                    return category, sub_category
        except Exception as exc:
            logger.warning("Ollama classification request failed: %s", exc)

        return "ECONOMIC", "GENERAL"
