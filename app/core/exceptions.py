class AppError(Exception):
    """Base class for application exceptions."""
    pass

class ConfigurationError(AppError):
    """Raised when critical configuration is missing."""
    pass

class AdapterError(AppError):
    """Raised when an external adapter fails (WA, IG, Email)."""
    pass

class DatabaseError(AppError):
    """Raised when database operation fails."""
    pass