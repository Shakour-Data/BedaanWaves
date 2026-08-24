from typing import Generic, TypeVar, Optional, Any

T = TypeVar('T')

class Result(Generic[T]):
    """
    Result pattern implementation for handling operation outcomes.
    Follows Clean OO principles by avoiding exceptions for expected business rule violations.
    """
    
    def __init__(
        self, 
        is_success: bool, 
        value: Optional[T] = None, 
        error_message: Optional[str] = None, 
        error_code: Optional[str] = None
    ):
        self._is_success = is_success
        self._value = value
        self._error_message = error_message
        self._error_code = error_code

    @property
    def is_success(self) -> bool:
        return self._is_success

    @property
    def is_failure(self) -> bool:
        return not self._is_success

    @property
    def value(self) -> T:
        if not self._is_success:
            raise ValueError("Cannot access value of a failed result.")
        return self._value # type: ignore

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message

    @property
    def error_code(self) -> Optional[str]:
        return self._error_code

    @staticmethod
    def success(value: T) -> 'Result[T]':
        return Result(True, value=value)

    @staticmethod
    def failure(error_message: str, error_code: str) -> 'Result[Any]':
        return Result(False, error_message=error_message, error_code=error_code)
