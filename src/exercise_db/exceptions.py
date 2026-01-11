"""Custom exceptions for ExerciseDB client"""


class ExerciseDBError(Exception):
    """Base exception for ExerciseDB errors"""

    pass


class ValidationError(ExerciseDBError):
    """Raised when validation fails"""

    pass


class APIError(ExerciseDBError):
    """Raised when API request fails"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class CacheError(ExerciseDBError):
    """Raised when cache operations fail"""

    pass
