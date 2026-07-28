"""
Chatbot Service - Tier 5 NLP Service

AI-powered chatbot for user assistance and financial Q&A.
Provides context-aware responses about markets, stocks, and platform features.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from ..core import BaseService


class ChatbotService(BaseService):
    """
    AI chatbot service for financial assistance.
    
    Capabilities:
    - Financial Q&A
    - Market data queries
    - Platform help and guidance
    - Persian and English support
    - Context-aware conversations
    """
    
    INTENT_PATTERNS = {
        "stock_price": ["قیمت", "price", "نرخ", "worth", "cost of"],
        "market_overview": ["بازار", "market", "overview", "summary", "وضعیت"],
        "portfolio": ["پرتفوی", "portfolio", "دارایی", "holdings", "سهام"],
        "analysis": ["تحلیل", "analysis", "score", "نمره", "سیگنال", "signal"],
        "news": ["خبر", "news", "اخبار", "اطلاعیه"],
        "help": ["کمک", "help", "راهنما", "چطور", "how to", "guidance"],
        "greeting": ["سلام", "hello", "hi", "hey", "درود"],
        "goodbye": ["خداحافظ", "bye", "goodbye", "خدانگهدار"],
    }
    
    FINANCIAL_RESPONSES = {
        "stock_price": "برای دریافت قیمت لحظه‌ای نماد، از صفحه جزئیات سهام استفاده کنید یا از دستور `/price <symbol>` کمک بگیرید.",
        "market_overview": "وضعیت کلی بازار را می‌توانید در داشبورد مشاهده کنید. برای تحلیل دقیق‌تر از بخش تحلیل استفاده کنید.",
        "portfolio": "برای مدیریت پرتفوی خود به بخش «پرتفوی» مراجعه کنید. می‌توانید سهام اضافه، حذف یا تحلیل کنید.",
        "analysis": "سیستم تحلیل ۶ بعدی ما نمرات جامعی از تحلیل تکنیکال، بنیادی، ریسک،sentiment، ماکرو و هوش مصنوعی ارائه می‌دهد.",
        "news": "آخرین اخبار مالی در بخش اخبار موجود است. تحلیل sentimen برای هر نماد نیز قابل مشاهده است.",
        "help": "من می‌توانم در موارد زیر کمک کنم: قیمت سهام، تحلیل بازار، مدیریت پرتفوی، اخبار و تحلیل‌ها. سوال خود را بپرسید!",
        "greeting": "سلام! به پلتفرم تحلیل بازار BedaanWaves خوش آمدید. چطور می‌توانم کمک کنم؟",
        "goodbye": "خداحافظ! موفق باشید.",
    }
    
    def __init__(self, service_name: str = "ChatbotService"):
        super().__init__(service_name)
        self._conversation_history: List[Dict[str, Any]] = []
        self._max_history = 50
    
    async def initialize(self) -> None:
        """Initialize chatbot service"""
        self._conversation_history.clear()
        self.logger.info("ChatbotService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown chatbot service"""
        self._conversation_history.clear()
        self.logger.info("ChatbotService shutdown")
    
    async def chat(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a chat message and generate response.
        
        Args:
            data: Dictionary with 'message', optional 'user_id', 'context'
            
        Returns:
            Chat response with message, intent, and suggestions
        """
        message = data.get("message", "")
        user_id = data.get("user_id", "anonymous")
        context = data.get("context", {})
        
        if not message:
            return {
                "response": "لطفا پیام خود را وارد کنید.",
                "intent": "unknown",
                "confidence": 0.0,
                "suggestions": ["قیمت سهام", "تحلیل بازار", "پرتفوی من"],
            }
        
        intent, confidence = self._detect_intent(message)
        response = self._generate_response(message, intent, context)
        
        self._conversation_history.append({
            "user_id": user_id,
            "message": message,
            "response": response,
            "intent": intent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        if len(self._conversation_history) > self._max_history:
            self._conversation_history.pop(0)
        
        suggestions = self._get_suggestions(intent)
        
        return {
            "response": response,
            "intent": intent,
            "confidence": confidence,
            "suggestions": suggestions,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def _detect_intent(self, message: str) -> tuple:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        best_intent = "unknown"
        best_score = 0.0
        
        for intent, keywords in self.INTENT_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in message_lower)
            normalized_score = score / max(len(keywords), 1)
            if normalized_score > best_score:
                best_score = normalized_score
                best_intent = intent
        
        return best_intent, min(best_score, 1.0)
    
    def _generate_response(self, message: str, intent: str, context: Dict[str, Any]) -> str:
        """Generate response based on intent"""
        if intent in self.FINANCIAL_RESPONSES:
            return self.FINANCIAL_RESPONSES[intent]
        
        if "?" in message or "؟" in message:
            return "سوال خوبی پرسیدید. برای دریافت اطلاعات دقیق‌تر می‌توانید از منوهای صفحه استفاده کنید یا جزئیات سهام را بررسی کنید."
        
        return "متوجه شدم. برای اطلاعات بیشتر می‌توانید از دستورات منو کمک بگیرید."
    
    def _get_suggestions(self, intent: str) -> List[str]:
        """Get follow-up suggestions based on intent"""
        suggestion_map = {
            "stock_price": ["تحلیل نماد", "نمودار قیمت", "اخبار نماد"],
            "market_overview": ["بازارهای جهانی", "بیشتر حرکتی", "تحلیل تکنیکال"],
            "portfolio": ["اضافه کردن سهام", "تحلیل ریسک", "بهینه‌سازی پرتفوی"],
            "analysis": ["نمودارهای تکنیکال", "اسکور ۶ بعدی", "پیش‌بینی قیمت"],
            "news": ["تحلیل sentimen", "خبرهای مهم", "تأثیر خبر"],
            "help": ["راهنمای استفاده", "سوالات متداول", "تماس با پشتیبانی"],
        }
        
        if intent == "greeting":
            return ["قیمت سهام", "تحلیل بازار", "پرتفوی من"]
        
        return suggestion_map.get(intent, ["قیمت سهام", "تحلیل بازار", "کمک"])
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of conversation messages
        """
        user_history = [
            msg for msg in self._conversation_history
            if msg.get("user_id") == user_id
        ]
        return user_history[-limit:]
    
    async def clear_history(self, user_id: str) -> Dict[str, Any]:
        """
        Clear conversation history for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Status of the operation
        """
        self._conversation_history = [
            msg for msg in self._conversation_history
            if msg.get("user_id") != user_id
        ]
        return {
            "status": "success",
            "message": "تاریخچه گفتگو پاک شد.",
            "user_id": user_id,
        }
