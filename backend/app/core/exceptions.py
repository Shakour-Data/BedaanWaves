"""
Domain Exceptions - Clean Code compliant exception hierarchy

All domain-specific exceptions inherit from BedaanWavesDomainException.
This allows catching domain errors specifically without catching generic Exception.
"""


class BedaanWavesDomainException(Exception):
    """Base exception for all BedaanWaves domain errors."""
    pass


class FinancialDataException(BedaanWavesDomainException):
    """Base exception for financial data operations."""
    pass


class DataProviderException(FinancialDataException):
    """Raised when a data provider fails to fetch data."""
    pass


class DataParsingException(FinancialDataException):
    """Raised when financial data cannot be parsed."""
    pass


class MarketDataException(BedaanWavesDomainException):
    """Base exception for market data operations."""
    pass


class AssetNotFoundException(MarketDataException):
    """Raised when an asset/symbol is not found."""
    pass


class MarketDataNotFoundException(MarketDataException):
    """Raised when market data is not available for a symbol."""
    pass


class IngestionException(MarketDataException):
    """Raised when data ingestion fails."""
    pass


class ValidationException(BedaanWavesDomainException):
    """Base exception for validation errors."""
    pass


class DataIntegrityException(ValidationException):
    """Raised when data integrity checks fail."""
    pass


class ConfigurationException(BedaanWavesDomainException):
    """Raised when configuration is invalid or missing."""
    pass


class ExternalServiceException(BedaanWavesDomainException):
    """Base exception for external service failures."""
    pass


class APIRateLimitException(ExternalServiceException):
    """Raised when external API rate limit is exceeded."""
    pass


class APIConnectionException(ExternalServiceException):
    """Raised when external API connection fails."""
    pass


class APIResponseException(ExternalServiceException):
    """Raised when external API returns an error response."""
    pass


class MLModelException(BedaanWavesDomainException):
    """Base exception for ML model operations."""
    pass


class ModelTrainingException(MLModelException):
    """Raised when model training fails."""
    pass


class ModelPredictionException(MLModelException):
    """Raised when model prediction fails."""
    pass


class CoefficientException(MLModelException):
    """Raised when coefficient operations fail."""
    pass


class ScoringException(BedaanWavesDomainException):
    """Raised when scoring calculations fail."""
    pass


class AnalysisException(BedaanWavesDomainException):
    """Base exception for analysis operations."""
    pass


class FundamentalAnalysisException(AnalysisException):
    """Raised when fundamental analysis fails."""
    pass


class TechnicalAnalysisException(AnalysisException):
    """Raised when technical analysis fails."""
    pass


class CryptoException(BedaanWavesDomainException):
    """Base exception for cryptocurrency operations."""
    pass


class CryptoDataException(CryptoException):
    """Raised when crypto data operations fail."""
    pass


class NotificationException(BedaanWavesDomainException):
    """Raised when notification delivery fails."""
    pass


class UserException(BedaanWavesDomainException):
    """Base exception for user operations."""
    pass


class UserNotFoundException(UserException):
    """Raised when a user is not found."""
    pass


class AuthorizationException(UserException):
    """Raised when authorization fails."""
    pass
