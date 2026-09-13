from datetime import datetime, timezone

class DomainException(Exception):
    """
    Base class for all domain-specific exceptions.
    Ensures consistent logging and context for errors.
    """
    
    def __init__(self, message: str, code: str, context: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)

    def __str__(self):
        return f"[{self.code}] {self.message} (Context: {self.context})"

class EntityNotFoundException(DomainException):
    """Thrown when a domain entity cannot be found."""
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(
            f"{entity_name} with identifier {identifier} not found.",
            "ENTITY_NOT_FOUND",
            {"entity": entity_name, "id": identifier}
        )

class ValidationException(DomainException):
    """Thrown when domain validation fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)
