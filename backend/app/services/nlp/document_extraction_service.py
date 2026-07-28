"""
Document Extraction Service - Tier 5 NLP Service

Extracts structured information from unstructured financial documents.
Supports PDFs, HTML pages, and plain text with entity recognition.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from ..core import BaseService


class DocumentExtractionService(BaseService):
    """
    Document extraction service for financial documents.
    
    Capabilities:
    - Entity extraction (companies, amounts, dates)
    - Financial metric extraction
    - Table data extraction
    - Multi-format support (text, HTML)
    - Persian document support
    """
    
    ENTITY_TYPES = {
        "company": ["شرکت", "شرکت", "company", "corp", "inc", "ltd"],
        "amount": ["ریال", "تومان", "million", "billion", "USD", "IRR"],
        "date": ["تاریخ", "date", "year", "month", "day"],
        "percentage": ["درصد", "percent", "%", "growth", "decline"],
        "currency": ["تومان", "ریال", "USD", "EUR", "rial", "toman"],
    }
    
    def __init__(self, service_name: str = "DocumentExtractionService"):
        super().__init__(service_name)
        self._extraction_patterns = self._build_patterns()
    
    async def initialize(self) -> None:
        """Initialize document extraction service"""
        self.logger.info("DocumentExtractionService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown document extraction service"""
        self._extraction_patterns.clear()
        self.logger.info("DocumentExtractionService shutdown")
    
    def _build_patterns(self) -> Dict[str, List[str]]:
        """Build entity extraction patterns"""
        return self.ENTITY_TYPES.copy()
    
    async def extract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from a document.
        
        Args:
            data: Dictionary with 'content', optional 'document_type', 'language'
            
        Returns:
            Extracted entities and structured data
        """
        content = data.get("content", "")
        document_type = data.get("document_type", "text")
        language = data.get("language", "auto")
        
        if not content:
            return {
                "entities": {},
                "tables": [],
                "summary": "",
                "document_type": document_type,
                "language": language,
            }
        
        entities = self._extract_entities(content)
        tables = self._extract_tables(content) if document_type in ["pdf", "html"] else []
        
        return {
            "entities": entities,
            "tables": tables,
            "summary": content[:500] + "..." if len(content) > 500 else content,
            "document_type": document_type,
            "language": self._detect_language(content),
            "entity_count": sum(len(v) for v in entities.values()),
            "table_count": len(tables),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract named entities from content"""
        entities: Dict[str, List[str]] = {}
        content_lower = content.lower()
        
        for entity_type, keywords in self._extraction_patterns.items():
            found = []
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    found.append(keyword)
            if found:
                entities[entity_type] = list(set(found))
        
        return entities
    
    def _extract_tables(self, content: str) -> List[Dict[str, Any]]:
        """Extract table structures from content"""
        tables = []
        lines = content.split("\n")
        
        current_table = []
        for line in lines:
            if "|" in line or "\t" in line:
                cells = [cell.strip() for cell in line.split("|") if cell.strip()]
                if cells:
                    current_table.append(cells)
            elif current_table:
                if len(current_table) > 1:
                    tables.append({
                        "headers": current_table[0],
                        "rows": current_table[1:],
                        "row_count": len(current_table) - 1,
                    })
                current_table = []
        
        if current_table and len(current_table) > 1:
            tables.append({
                "headers": current_table[0],
                "rows": current_table[1:],
                "row_count": len(current_table) - 1,
            })
        
        return tables
    
    def _detect_language(self, text: str) -> str:
        """Detect document language"""
        persian_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
        return "fa" if persian_chars > len(text) * 0.3 else "en"
    
    async def extract_financial_metrics(self, content: str) -> Dict[str, Any]:
        """
        Extract financial metrics from document content.
        
        Args:
            content: Document text content
            
        Returns:
            Extracted financial metrics
        """
        metrics = {
            "revenue": None,
            "profit": None,
            "eps": None,
            "pe_ratio": None,
            "market_cap": None,
            "dividend_yield": None,
        }
        
        import re
        
        patterns = {
            "revenue": r"revenue[:\s]+[\d,\.]+\s*(billion|million|B|M)?\s*(USD|IRR|toman)?",
            "profit": r"(net profit|net income|سود خالص)[:\s]+[\d,\.]+\s*(billion|million|B|M)?",
            "eps": r"EPS[:\s]+[\d,\.]+",
            "pe_ratio": r"P/E[:\s]+[\d,\.]+",
            "market_cap": r"market cap[:\s]+[\d,\.]+\s*(billion|million|B|M)?",
            "dividend_yield": r"dividend[:\s]+[\d,\.]+%?",
        }
        
        for metric, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metrics[metric] = match.group(0)
        
        return {
            "metrics": {k: v for k, v in metrics.items() if v is not None},
            "found_count": sum(1 for v in metrics.values() if v is not None),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }
    
    async def batch_extract(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract data from multiple documents.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of extraction results
        """
        import asyncio
        tasks = [self.extract(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed = []
        for doc, result in zip(documents, results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch extract error: {result}")
                processed.append({"error": str(result), "title": doc.get("title")})
            else:
                processed.append(result)
        
        return processed
