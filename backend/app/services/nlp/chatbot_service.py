"""
Chatbot Service - Tier 5 NLP Service

Conversational AI for financial Q&A over market data, news, and scoring.
Supports multi-turn conversations with context retention and
language detection (English and Persian).
"""

import asyncio
from typing import Any

from app.core.utils import utc_now_iso

from ..core import AnalysisService


class ChatbotService(AnalysisService):
    """
    Financial chatbot service for market-related Q&A.

    Capabilities:
    - Multi-turn conversation with context management
    - Language-aware responses (English / Persian)
    - Integration with news, scoring, and technical analysis services
    - Conversation history tracking
    """

    SUPPORTED_LANGUAGES = ["en", "fa"]
    DEFAULT_MAX_HISTORY = 10
    GREETING_KEYWORDS = {"hello", "hi", "hey", "سلام", "درود"}
    FAREWELL_KEYWORDS = {"bye", "goodbye", "exit", "خداحافظ", "پایان"}

    def __init__(
        self,
        service_name: str = "ChatbotService",
        max_history: int = DEFAULT_MAX_HISTORY,
        scoring_service: Any | None = None,
        news_service: Any | None = None,
    ):
        super().__init__(service_name)
        self.max_history = max_history
        self.scoring_service = scoring_service
        self.news_service = news_service
        self._sessions: dict[str, list[dict[str, Any]]] = {}

    async def initialize(self) -> None:
        self.logger.info("ChatbotService initialized")

    async def shutdown(self) -> None:
        self._sessions.clear()
        self.logger.info("ChatbotService shutdown")

    def _detect_language(self, text: str) -> str:
        if not text:
            return "en"
        persian_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
        return "fa" if persian_chars > len(text) * 0.3 else "en"

    def _get_session(self, session_id: str) -> list[dict[str, Any]]:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return self._sessions[session_id]

    def _prune_session(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(history) > self.max_history:
            return history[-self.max_history:]
        return history

    async def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Use chat() instead of analyze() for ChatbotService")

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        symbol: str | None = None,
    ) -> dict[str, Any]:
        session = self._get_session(session_id)
        session.append({"role": "user", "content": message, "timestamp": utc_now_iso()})
        session = self._prune_session(session)

        response = await self._generate_response(message, session, symbol)

        session.append({"role": "assistant", "content": response["text"], "timestamp": utc_now_iso()})
        session = self._prune_session(session)

        return {
            "session_id": session_id,
            "response": response["text"],
            "language": response["language"],
            "symbol": symbol,
            "context_summary": {
                "history_length": len(session),
                "has_scoring_context": any("score" in m.get("content", "").lower() for m in session),
            },
            "timestamp": utc_now_iso(),
        }

    async def _generate_response(
        self,
        message: str,
        session: list[dict[str, Any]],
        symbol: str | None,
    ) -> dict[str, Any]:
        msg_lower = message.lower().strip()
        lang = self._detect_language(message)

        if msg_lower in self.GREETING_KEYWORDS:
            text = "سلام! در خدمتم. سؤالات مرا سؤال بازارهای مالی یا سهام بپرسید." if lang == "fa" else "Hello! I'm here to help with financial market questions. Ask me about stocks, scores, or news."
        elif msg_lower in self.FAREWELL_KEYWORDS:
            text = "خداحافظ! امیدوارم کمک‌کننده بوده باشم." if lang == "fa" else "Goodbye! Hope I was helpful."
        elif symbol and self.scoring_service:
            try:
                score_result = await self._query_scoring(symbol)
                text = self._format_score_response(score_result, lang)
            except Exception as exc:
                self.logger.warning(f"Score query failed for {symbol}: {exc}")
                text = self._default_response(lang)
        else:
            text = self._default_response(lang)

        return {"text": text, "language": lang}

    async def _query_scoring(self, symbol: str) -> dict[str, Any]:
        if hasattr(self.scoring_service, "analyze"):
            return await self.scoring_service.analyze({"symbol": symbol})
        return {"symbol": symbol, "score": 0, "grade": "N/A"}

    def _format_score_response(self, score_result: dict[str, Any], lang: str) -> str:
        score = score_result.get("score", score_result.get("overall_score", 0))
        grade = score_result.get("grade", "N/A")
        if lang == "fa":
            return f"امتیاز {score_result.get('symbol', '')}: {score} (نمره: {grade})"
        return f"Score for {score_result.get('symbol', '')}: {score} (Grade: {grade})"

    def _default_response(self, lang: str) -> str:
        if lang == "fa":
            return "متوجه سؤال شما نمی‌شوم. می‌توانید درباره سهام، امتیازها یا اخبار بپرسید."
        return "I'm not sure I understand. You can ask me about stocks, scores, or news."

    async def clear_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def batch_chat(
        self,
        messages: list[dict[str, Any]],
        session_id: str = "default",
    ) -> list[dict[str, Any]]:
        tasks = [
            self.chat(
                msg.get("message", ""),
                session_id=session_id,
                symbol=msg.get("symbol"),
            )
            for msg in messages
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        processed = []
        for msg, result in zip(messages, results):
            if isinstance(result, Exception):
                processed.append({"error": str(result), "message": msg.get("message", "")})
            else:
                processed.append(result)
        return processed

    async def health_check(self) -> dict[str, Any]:
        base = await super().health_check()
        base.update({
            "source": "ChatbotService",
            "active_sessions": len(self._sessions),
            "max_history": self.max_history,
        })
        return base
