"""
Multilingual News Service - Tier 5 NLP Service

Provides localized financial news processing with language detection,
translation, and country-specific news categorization.
"""

from typing import Dict, List, Optional, Any
from datetime import timezone, datetime
import asyncio
from app.services.core.base_service import BaseService
from app.services.nlp.sentiment_analysis_service import SentimentAnalysisService
from app.services.nlp.news_summarization_service import NewsSummarizationService
import logging

class MultilingualNewsService(BaseService):
    """
    Multilingual News Service.
    
    Processes financial news in multiple languages with:
    - Language detection
    - Translation capabilities
    - Country/region-specific news categorization
    - Sentiment analysis per language
    """
    
    def __init__(self,
                 service_name: str = "MultilingualNewsService",
                 sentiment_service: Optional[SentimentAnalysisService] = None,
                 summarization_service: Optional[NewsSummarizationService] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize multilingual news service.
        
        Args:
            service_name: Service identifier
            sentiment_service: Sentiment analysis service instance
            summarization_service: News summarization service instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.sentiment_service = sentiment_service or SentimentAnalysisService()
        self.summarization_service = summarization_service or NewsSummarizationService()
        
        # Supported languages
        self.supported_languages = {
            "fa": "Persian/Farsi",
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "ru": "Russian",
            "tr": "Turkish",
            "pt": "Portuguese"
        }
        
        # Country-language mappings
        self.country_languages = {
                        "USA": ["en"],
            "UK": ["en"],
            "Germany": ["de", "en"],
            "France": ["fr", "en"],
            "Spain": ["es", "en"],
            "China": ["zh", "en"],
            "Japan": ["ja", "en"],
            "Korea": ["ko", "en"],
            "Turkey": ["tr", "en"],
            "Brazil": ["pt", "en"],
            "Russia": ["ru", "en"],
            "Saudi Arabia": ["ar", "en"],
            "UAE": ["ar", "en"],
        }
        
        # News sources by country
        self.country_news_sources = {
                        "USA": ["Reuters", "Bloomberg", "CNBC", "WSJ"],
            "UK": ["Reuters", "Bloomberg", "Financial_Times"],
            "Germany": ["Handelsblatt", "Frankfurter_Allgemeine"],
            "France": ["Les_Echos", "BFM_Business"],
            "Japan": ["Nikkei", "Bloomberg_Japan"],
        }
    
    async def initialize(self) -> None:
        """Initialize multilingual news service."""
        self.logger.info("Initializing MultilingualNewsService")
        await self.sentiment_service.initialize()
        await self.summarization_service.initialize()
        self.logger.info("MultilingualNewsService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown multilingual news service."""
        await self.sentiment_service.shutdown()
        await self.summarization_service.shutdown()
        self.logger.info("MultilingualNewsService shutdown")
    
    async def detect_language(self, text: str) -> str:
        """
        Detect the language of a given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code (e.g., "en", "fa")
        """
        # Simplified language detection
        # In production, would use libraries like langdetect or polyglot
        
        # Persian character detection disabled (legacy, requires non-English chars)

        # Check for common English words
        english_words = ["the", "and", "of", "to", "in", "for", "is", "on", "with", "at", "by", "an", "this", "that"]
        text_lower = text.lower()
        english_matches = sum(1 for word in english_words if word in text_lower)
        if english_matches >= 3:
            return "en"

        # Default to English
        return "en"
    
    async def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code
            
        Returns:
            Translated text
        """
        # In production, would integrate with translation APIs
        # For now, return original text with a note
        self.logger.info(f"Translation requested to {target_language}")
        return text
    
    async def process_news_for_country(self,
                                       country: str,
                                       news_items: List[Dict[str, Any]],
                                       target_language: str = None) -> List[Dict[str, Any]]:
        """
        Process news items for a specific country.
        
        Args:
            country: Country name
            news_items: List of news items to process
            target_language: Target language for output (defaults to country's primary language)
            
        Returns:
            Processed news items with sentiment and summaries
        """
        if target_language is None:
            # Get primary language for country
            langs = self.country_languages.get(country, ["en"])
            target_language = langs[0]
        
        processed_news = []
        
        for item in news_items:
            try:
                # Detect original language
                original_lang = await self.detect_language(item.get("title", "") + " " + item.get("body", ""))
                
                # Translate if needed
                translated_title = item.get("title", "")
                translated_body = item.get("body", "")
                
                if original_lang != target_language:
                    translated_title = await self.translate_text(item.get("title", ""), target_language)
                    translated_body = await self.translate_text(item.get("body", ""), target_language)
                
                # Get sentiment
                sentiment_result = await self.sentiment_service.analyze(
                    translated_title + " " + translated_body
                )
                
                # Generate summary
                summary_result = await self.summarization_service.summarize(
                    translated_body,
                    max_length=150
                )
                
                processed_item = {
                    **item,
                    "original_language": original_lang,
                    "target_language": target_language,
                    "translated_title": translated_title,
                    "translated_body": translated_body,
                    "sentiment": sentiment_result,
                    "summary": summary_result,
                    "country": country,
                    "processed_at": datetime.now(timezone.utc).isoformat()
                }
                
                processed_news.append(processed_item)
                
            except Exception as e:
                self.logger.error(f"Error processing news item: {str(e)}")
                processed_news.append({
                    **item,
                    "error": str(e),
                    "country": country
                })
        
        return processed_news
    
    async def get_news_by_country(self,
                                  countries: List[str],
                                  categories: List[str] = None,
                                  limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get news for multiple countries.
        
        Args:
            countries: List of country names
            categories: News categories to filter
            limit: Maximum news items per country
            
        Returns:
            Dictionary mapping country to processed news items
        """
        result = {}
        
        for country in countries:
            # Get news sources for country
            sources = self.country_news_sources.get(country, [])
            
            # Fetch news from sources (simplified)
            news_items = await self._fetch_news_from_sources(sources, categories, limit)
            
            # Process for country
            processed = await self.process_news_for_country(country, news_items)
            
            result[country] = processed
        
        return result
    
    async def _fetch_news_from_sources(self,
                                       sources: List[str],
                                       categories: List[str] = None,
                                       limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch news from specified sources.
        
        Args:
            sources: List of news source names
            categories: Categories to filter
            limit: Maximum items to fetch
            
        Returns:
            List of raw news items
        """
        # In production, would integrate with actual news APIs
        # This is a placeholder implementation
        return []
    
    async def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages.
        
        Returns:
            Dictionary mapping language codes to language names
        """
        return self.supported_languages
    
    async def get_country_languages(self, country: str) -> List[str]:
        """
        Get supported languages for a country.
        
        Args:
            country: Country name
            
        Returns:
            List of language codes supported for the country
        """
        return self.country_languages.get(country, ["en"])

# Factory function for dependency injection
def get_multilingual_news_service(sentiment_service=None,
                                   summarization_service=None,
                                   logger=None) -> MultilingualNewsService:
    """Factory function to create MultilingualNewsService instance."""
    return MultilingualNewsService(
        service_name="MultilingualNewsService",
        sentiment_service=sentiment_service,
        summarization_service=summarization_service,
        logger=logger
    )