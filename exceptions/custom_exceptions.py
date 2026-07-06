"""Custom exception hierarchy for the SDMS.

Every module-specific exception inherits from a common
:class:`SDMSException` base so that callers can catch all
application-level errors with a single ``except SDMSException``
when desired.
"""

from __future__ import annotations


class SDMSException(Exception):
    """Base exception for all Secure Document Management System errors."""


class AuthenticationError(SDMSException):
    """Raised when user authentication fails (login, token validation, etc.)."""


class AuthorizationError(SDMSException):
    """Raised when an authenticated user lacks permission for an operation."""


class CryptographicError(SDMSException):
    """Raised when an encryption, decryption, or key-management operation fails."""


class DatabaseError(SDMSException):
    """Raised when a database operation fails (connection, query, integrity)."""


class FileHandlingError(SDMSException):
    """Raised when file read, write, or transfer operations fail."""


class ValidationError(SDMSException):
    """Raised when input data fails validation rules."""
