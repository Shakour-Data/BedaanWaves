from typing import Generic, TypeVar, Optional as PyOptional, Callable, Any

T = TypeVar('T')
U = TypeVar('U')

class Optional(Generic[T]):
    """
    Optional pattern implementation for null safety.
    Provides a way to handle potentially missing values without returning None.
    """
    
    def __init__(self, value: PyOptional[T], has_value: bool):
        self._value = value
        self._has_value = has_value

    @property
    def has_value(self) -> bool:
        return self._has_value

    @property
    def is_none(self) -> bool:
        return not self._has_value

    @staticmethod
    def some(value: T) -> 'Optional[T]':
        if value is None:
            raise ValueError("Optional.some() cannot be called with None.")
        return Optional(value, True)

    @staticmethod
    def none() -> 'Optional[Any]':
        return Optional(None, False)

    def get_or_else(self, default_value: T) -> T:
        return self._value if self._has_value else default_value

    def map(self, mapper: Callable[[T], U]) -> 'Optional[U]':
        if not self._has_value:
            return Optional.none()
        return Optional.some(mapper(self._value)) # type: ignore

    def flat_map(self, mapper: Callable[[T], 'Optional[U]']) -> 'Optional[U]':
        if not self._has_value:
            return Optional.none()
        return mapper(self._value) # type: ignore
