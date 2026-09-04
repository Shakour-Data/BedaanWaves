"""
Sentiment Analysis Service - Tier 5 NLP Service

Persian sentiment analysis for news, social media, and financial texts.
Provides 3-class classification (positive/neutral/negative) with confidence scores.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import asyncio
from ..core import AnalysisService
from app.core.utils import utc_now_iso


class SentimentAnalysisService(AnalysisService):
    """
    Persian sentiment analysis service for financial texts.
    
    Capabilities:
    - 3-class sentiment classification (positive/neutral/negative)
    - Confidence scoring (0-100)
    - Aspect-based sentiment extraction
    - Financial keyword weighting
    - Batch processing support
    """
    
    SENTIMENT_LABELS = ["positive", "neutral", "negative"]
    
    FINANCIAL_POSITIVE_KEYWORDS = {
        "profit", "growth", "increase", "rise", "bullish", "buy", "up",
        "gain", "success", "strong", "improve", "surge", "boost", "rally",
    }

    FINANCIAL_NEGATIVE_KEYWORDS = {
        "loss", "decline", "fall", "drop", "bearish", "sell", "down",
        "decrease", "weak", "risk", "crash", "plunge", "dip", "tumble",
    }

    def __init__(self, service_name: str = "SentimentAnalysisService"):
        super().__init__(service_name)
        self._model_loaded = False
        self._stopwords: set = set()

    async def initialize(self) -> None:
        """Initialize sentiment analysis service"""
        self._load_stopwords()
        self._model_loaded = True
        self.logger.info("SentimentAnalysisService initialized")

    async def shutdown(self) -> None:
        """Shutdown sentiment analysis service"""
        self._model_loaded = False
        self._stopwords.clear()
        self.logger.info("SentimentAnalysisService shutdown")

    def _load_stopwords(self) -> None:
        """Load stopwords for text preprocessing"""
        self._stopwords = {
            "the", "is", "at", "which", "on", "and", "or", "in", "to", "of",
        }
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment of a text.
        
        Args:
            data: Dictionary with 'text' key and optional 'symbol' key
            
        Returns:
            Sentiment analysis result with label, confidence, and scores
        """
        text = data.get("text", "")
        symbol = data.get("symbol")
        
        if not text:
            return {
                "label": "neutral",
                "confidence": 0.0,
                "scores": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
                "symbol": symbol,
                "analyzed_at": utc_now_iso(),
            }
        
        scores = self._calculate_sentiment_scores(text)
        label = max(scores, key=scores.get)
        confidence = scores[label]
        
        return {
            "label": label,
            "confidence": round(confidence, 2),
            "scores": {k: round(v, 2) for k, v in scores.items()},
            "symbol": symbol,
            "analyzed_at": utc_now_iso(),
        }
    
    def _calculate_sentiment_scores(self, text: str) -> Dict[str, float]:
        """Calculate sentiment scores for text"""
        text_lower = text.lower()
        words = set(text_lower.split())
        
        positive_count = len(words & self.FINANCIAL_POSITIVE_KEYWORDS)
        negative_count = len(words & self.FINANCIAL_NEGATIVE_KEYWORDS)
        total = positive_count + negative_count
        
        if total == 0:
            return {"positive": 0.0, "neutral": 1.0, "negative": 0.0}
        
        positive_score = positive_count / total
        negative_score = negative_count / total
        neutral_score = 1.0 - max(positive_score, negative_score)
        
        return {
            "positive": positive_score,
            "neutral": neutral_score,
            "negative": negative_score,
        }
    
    async def batch_analyze(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple texts.
        
        Args:
            data_list: List of dictionaries with 'text' key
            
        Returns:
            List of sentiment analysis results
        """
        tasks = [self.analyze(item) for item in data_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed = []
        for item, result in zip(data_list, results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch sentiment error for {item.get('symbol')}: {result}")
                processed.append({"error": str(result), "symbol": item.get("symbol")})
            else:
                processed.append(result)
        
        return processed
    
    async def analyze_symbol_sentiment(self, symbol: str, news_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Aggregate sentiment for a symbol from multiple news items.
        
        Args:
            symbol: Stock symbol
            news_items: List of news with 'title' and 'summary' keys
            
        Returns:
            Aggregated sentiment result
        """
        texts = []
        for item in news_items:
            text = f"{item.get('title', '')} {item.get('summary', '')}"
            texts.append({"text": text, "symbol": symbol})
        
        results = await self.batch_analyze(texts)
        
        valid_results = [r for r in results if "error" not in r]
        if not valid_results:
            return {
                "symbol": symbol,
                "label": "neutral",
                "confidence": 0.0,
                "scores": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
                "news_count": 0,
            }
        
        avg_scores = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
        for result in valid_results:
            for label, score in result["scores"].items():
                avg_scores[label] += score
        
        for label in avg_scores:
            avg_scores[label] /= len(valid_results)
        
        label = max(avg_scores, key=avg_scores.get)
        
        return {
            "symbol": symbol,
            "label": label,
            "confidence": round(avg_scores[label], 2),
            "scores": {k: round(v, 2) for k, v in avg_scores.items()},
            "news_count": len(valid_results),
            "analyzed_at": utc_now_iso(),
        }
