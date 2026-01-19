"""
QuantGrid Core - Custom Exceptions
"""


class QuantGridException(Exception):
    """Base exception for all QuantGrid errors"""
    pass


class AuthenticationError(QuantGridException):
    """Raised when authentication fails"""
    pass


class ValidationError(QuantGridException):
    """Raised when data validation fails"""
    pass


class NotFoundError(QuantGridException):
    """Raised when a resource is not found"""
    pass


class RateLimitError(QuantGridException):
    """Raised when API rate limit is exceeded"""
    pass
