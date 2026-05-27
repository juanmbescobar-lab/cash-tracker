"""Domain-level exceptions raised by the service layer.

These are HTTP-agnostic: services raise them with semantic meaning
(e.g., "not found", "conflict"), and the API layer translates them
into HTTP responses via exception handlers registered on the FastAPI
application.

Decoupling services from HTTP allows:
- Reusing services from non-HTTP contexts (CLI scripts, background jobs).
- Testing services without ``TestClient``.
- Centralizing HTTP error translation in one place.
"""


class DomainError(Exception):
    """Base class for all domain exceptions."""


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, resource_id: int | str) -> None:
        super().__init__(f"{resource} with id {resource_id} not found")
        self.resource = resource
        self.resource_id = resource_id


class ConflictError(DomainError):
    """Raised when a request conflicts with current resource state.

    Examples: unique constraint violation, attempting to delete a
    resource still referenced by others.
    """


class BusinessRuleError(DomainError):
    """Raised when a request violates a domain rule.

    Examples: expense without category, invalid transition between
    states (when more complex workflows are introduced).
    """
