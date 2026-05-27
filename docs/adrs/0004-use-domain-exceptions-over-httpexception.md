# 0004 - Use custom domain exceptions over HTTPException in services

- **Status**: Accepted
- **Date**: 2026-05-23
- **Deciders**: Juan M. Bermúdez Escobar

## Context and Problem Statement

Service-layer functions need a way to communicate failure conditions
(resource not found, conflict with current state, business rule
violation) to the calling layer. In a FastAPI application, the most
direct option is to raise ``HTTPException`` from the service itself,
short-circuiting the request with an HTTP status code. The alternative
is to raise a domain-specific exception and translate it to HTTP at
the API layer via exception handlers.

We must choose a convention that all service functions follow.

## Decision Drivers

- Services should remain testable without an HTTP test client
- Services should be reusable from non-HTTP contexts (CLI scripts,
  scheduled jobs, background workers) without modification
- Error translation should be centralized
- API responses should be consistent across the application

## Considered Options

1. **Raise ``HTTPException`` directly from services**
2. **Define custom domain exceptions and translate them at the API layer**

## Decision Outcome

Chosen option: **custom domain exceptions translated at the API layer**.

Services raise ``NotFoundError``, ``ConflictError``, or
``BusinessRuleError`` (defined in ``app/core/exceptions.py``). FastAPI
exception handlers, registered in ``app/main.py``, translate these to
HTTP responses with the appropriate status codes (404, 409, 422).

This keeps the service layer free of HTTP concerns, which has three
concrete benefits:

1. **Services remain testable in isolation**. Unit tests for service
   functions can ``pytest.raises(NotFoundError)`` without needing
   ``TestClient`` or any HTTP infrastructure.
2. **Services can be reused outside HTTP**. A future CLI command or
   scheduled job can call ``create_transaction(db, data)`` and handle
   ``BusinessRuleError`` natively, without mocking HTTP responses.
3. **HTTP status code mapping is centralized**. If the team decides
   that ``ConflictError`` should return 422 instead of 409, the change
   is in one place (the exception handler), not scattered across
   every service function.

### Pros and Cons of the Options

**Option 1 — Raise ``HTTPException`` directly**

- ✅ Simpler: fewer files, one less layer of indirection
- ✅ No exception handler boilerplate
- ❌ Services tightly coupled to HTTP; cannot be reused elsewhere
- ❌ Tests require ``TestClient`` even for pure business logic
- ❌ HTTP status code decisions scattered across service functions

**Option 2 — Custom domain exceptions (chosen)**

- ✅ Services are HTTP-agnostic and reusable
- ✅ Unit-testable without ``TestClient``
- ✅ Centralized HTTP translation
- ✅ Semantic exceptions clearer than HTTP status codes
- ❌ One additional layer of indirection
- ❌ Exception handler boilerplate (~15 lines once)

## Consequences

- Every service function that can fail raises a ``DomainError``
  subclass, never ``HTTPException``.
- The router layer is thin: it parses input, calls services, and
  returns Pydantic schemas. Errors are not caught explicitly; they
  propagate to the registered exception handlers.
- New domain failure modes require defining a new ``DomainError``
  subclass and registering a handler for it.

## Re-evaluation Trigger

Reconsider this decision if:

- The application loses all non-HTTP entry points (no CLI, no jobs,
  no other consumers of services), making reusability moot.
- Exception handler boilerplate grows significantly (e.g., dozens of
  exception types with custom translation logic).
