from __future__ import annotations


class CrimeSafetyServiceError(Exception):
    """Base exception for crime metadata lookups."""


class CrosswalkNotFoundError(CrimeSafetyServiceError):
    """Raised when an ORI cannot be resolved from the crosswalk."""


class ExternalAPIError(CrimeSafetyServiceError):
    """Raised when external API calls fail."""


__all__ = [
    "CrimeSafetyServiceError",
    "CrosswalkNotFoundError",
    "ExternalAPIError",
]