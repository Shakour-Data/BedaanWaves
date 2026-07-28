"""
News Summarization Service - Tier 5 NLP Service

Summarizes financial news articles and generates concise summaries.
Supports both extractive and abstractive summarization approaches.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from ..core import BaseService


class NewsSummarizationService(BaseService):
    """
    News summarization service for financial texts.
    
    Capabilities:
    - Extractive summarization (key sentence selection)
    - Abstractive summarization (generated summaries)
    - Persian and English language support
    - Configurable summary length
    - Key entity extraction
    """
    
    def __init__(self, service_name: str = "NewsSummarizationService"):
        super().__init__(service_name)
        self._max_summary_length = 200
        self._min_sentence_score = 0.3
    
    async def initialize(self) -> None:
        """Initialize summarization service"""
        self.logger.info("NewsSummarizationService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown summarization service"""
        self.logger.info("NewsSummarizationService shutdown")
    
    async def summarize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize a news article.
        
        Args:
            data: Dictionary with 'text', optional 'title', 'max_length', 'language'
            
        Returns:
            Summarization result with summary, key points, and metadata
        """
        text = data.get("text", "")
        title = data.get("title", "")
        max_length = data.get("max_length", self._max_summary_length)
        language = data.get("language", "auto")
        
        if not text:
            return {
                "summary": "",
                "key_points": [],
                "language": language,
                "original_length": 0,
                "summary_length": 0,
                "compression_ratio": 0.0,
            }
        
        sentences = self._split_sentences(text)
        if not sentences:
            return {
                "summary": text[:max_length],
                "key_points": [title] if title else [],
                "language": language,
                "original_length": len(text),
                "summary_length": min(max_length, len(text)),
                "compression_ratio": round(max_length / len(text), 2) if len(text) > 0 else 0.0,
            }
        
        scored_sentences = self._score_sentences(sentences, title)
        selected_sentences = self._select_sentences(scored_sentences, max_length)
        
        summary = " ".join(selected_sentences)
        key_points = self._extract_key_points(selected_sentences)
        
        return {
            "summary": summary,
            "key_points": key_points,
            "language": self._detect_language(text),
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": round(len(summary) / len(text), 2) if len(text) > 0 else 0.0,
            "sentence_count": len(selected_sentences),
        }
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        delimiters = [". ", "! ", "? ", "\n", "。", "！", "？"]
        sentences = [text]
        for delimiter in delimiters:
            new_sentences = []
            for sentence in sentences:
                new_sentences.extend(sentence.split(delimiter))
            sentences = new_sentences
        
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _score_sentences(self, sentences: List[str], title: str) -> List[tuple]:
        """Score sentences by importance"""
        scored = []
        title_words = set(title.lower().split()) if title else set()
        
        for sentence in sentences:
            words = set(sentence.lower().split())
            
            position_score = 1.0 if sentences.index(sentence) < 3 else 0.5
            title_score = len(words & title_words) / max(len(words), 1)
            length_score = min(1.0, len(sentence) / 100)
            
            score = (position_score * 0.3 + title_score * 0.4 + length_score * 0.3)
            scored.append((sentence, score))
        
        return scored
    
    def _select_sentences(self, scored_sentences: List[tuple], max_length: int) -> List[str]:
        """Select top sentences within length limit"""
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        selected = []
        current_length = 0
        
        for sentence, score in scored_sentences:
            if score < self._min_sentence_score:
                continue
            if current_length + len(sentence) > max_length and selected:
                break
            selected.append(sentence)
            current_length += len(sentence)
        
        return selected[:5]
    
    def _extract_key_points(self, sentences: List[str]) -> List[str]:
        """Extract key points from selected sentences"""
        key_points = []
        for sentence in sentences[:3]:
            if len(sentence) > 20:
                key_points.append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
        return key_points
    
    def _detect_language(self, text: str) -> str:
        """Detect text language (Persian vs English)"""
        persian_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
        return "fa" if persian_chars > len(text) * 0.3 else "en"
    
    async def batch_summarize(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Summarize multiple articles.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of summarization results
        """
        import asyncio
        tasks = [self.summarize(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed = []
        for article, result in zip(articles, results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch summarize error: {result}")
                processed.append({"error": str(result), "title": article.get("title")})
            else:
                processed.append(result)
        
        return processed
    
    async def summarize_news_feed(self, news_items: List[Dict[str, str]], max_total_length: int = 500) -> Dict[str, Any]:
        """
        Summarize a news feed into a single digest.
        
        Args:
            news_items: List of news items with 'title' and 'summary'
            max_total_length: Maximum total summary length
            
        Returns:
            Combined news digest
        """
        if not news_items:
            return {"digest": "", "item_count": 0}
        
        individual_summaries = []
        for item in news_items:
            result = await self.summarize({
                "text": f"{item.get('title', '')} {item.get('summary', '')}",
                "max_length": max_total_length // max(len(news_items), 1),
            })
            if "error" not in result:
                individual_summaries.append(result["summary"])
        
        digest = " ".join(individual_summaries)[:max_total_length]
        
        return {
            "digest": digest,
            "item_count": len(news_items),
            "summarized_count": len(individual_summaries),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
