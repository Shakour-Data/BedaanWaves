"""
Domain Exceptions - Clean Code compliant exception hierarchy

All domain-specific exceptions inherit from BedaanWavesDomainException.
This allows catching domain errors specifically without catching generic Exception.
"""


class BedaanWavesDomainException(Exception):
    """Base exception for all BedaanWaves domain errors."""


class FinancialDataException(BedaanWavesDomainException):
    """Base exception for financial data operations."""


class DataProviderException(FinancialDataException):
    """Raised when a data provider fails to fetch data."""


class DataParsingException(FinancialDataException):
    """Raised when financial data cannot be parsed."""


class MarketDataException(BedaanWavesDomainException):
    """Base exception for market data operations."""


class AssetNotFoundException(MarketDataException):
    """Raised when an asset/symbol is not found."""


class MarketDataNotFoundException(MarketDataException):
    """Raised when market data is not available for a symbol."""


class IngestionException(MarketDataException):
    """Raised when data ingestion fails."""


class ValidationException(BedaanWavesDomainException):
    """Base exception for validation errors."""


class DataIntegrityException(ValidationException):
    """Raised when data integrity checks fail."""


class ConfigurationException(BedaanWavesDomainException):
    """Raised when configuration is invalid or missing."""


class ExternalServiceException(BedaanWavesDomainException):
    """Base exception for external service failures."""


class APIRateLimitException(ExternalServiceException):
    """Raised when external API rate limit is exceeded."""


class APIConnectionException(ExternalServiceException):
    """Raised when external API connection fails."""


class APIResponseException(ExternalServiceException):
    """Raised when external API returns an error response."""


class MLModelException(BedaanWavesDomainException):
    """Base exception for ML model operations."""


class ModelTrainingException(MLModelException):
    """Raised when model training fails."""


class ModelPredictionException(MLModelException):
    """Raised when model prediction fails."""


class CoefficientException(MLModelException):
    """Raised when coefficient operations fail."""


class ScoringException(BedaanWavesDomainException):
    """Raised when scoring calculations fail."""


class AnalysisException(BedaanWavesDomainException):
    """Base exception for analysis operations."""


class FundamentalAnalysisException(AnalysisException):
    """Raised when fundamental analysis fails."""


class TechnicalAnalysisException(AnalysisException):
    """Raised when technical analysis fails."""


class NotificationException(BedaanWavesDomainException):
    """Raised when notification delivery fails."""


class UserException(BedaanWavesDomainException):
    """Base exception for user operations."""


class UserNotFoundException(UserException):
    """Raised when a user is not found."""


class AuthorizationException(UserException):
    """Raised when authorization fails."""
