# ADR-0005: Adopt Test-Driven Development

## Status

Accepted

---

## Context

The project contains significant business logic around language learning,
adaptive practice, analytics, and conversational behaviour.

Previous experience demonstrated that introducing tests after implementation
results in reduced coverage and more difficult refactoring.

The project also aims to maintain a framework-independent domain model.

---

## Decision

The project will be developed using Test-Driven Development (TDD).

Domain behaviour will be implemented by writing tests before production code.

Testing priorities are:

1. Domain
2. Application
3. Infrastructure
4. End-to-End

Domain tests should execute without requiring external systems.

---

## Consequences

### Positive

- Domain design is driven by business behaviour.
- High confidence during refactoring.
- Better documentation of business rules.
- Faster feedback during development.

### Negative

- Initial development may be slower.
- Requires discipline throughout the project lifecycle.
