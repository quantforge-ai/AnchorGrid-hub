"""
AnchorGrid Core - Custom Exceptions
"""


class AnchorGridException(Exception):
    """Base exception for all AnchorGrid errors"""
    pass


class AuthenticationError(AnchorGridException):
    """Raised when authentication fails"""
    pass


class ValidationError(AnchorGridException):
    """Raised when data validation fails"""
    pass


class NotFoundError(AnchorGridException):
    """Raised when a resource is not found"""
    pass


class RateLimitError(AnchorGridException):
    """Raised when API rate limit is exceeded"""
    pass
