# ADR-0003: Use Repository and Data Mapper Patterns

## Status

Accepted

---

## Context

The domain model should not be coupled to persistence technology.

Business entities should not inherit from ORM classes or contain persistence
behaviour.

The project may evolve to use different persistence technologies without
requiring changes to the domain model.

---

## Decision

Persistence will be isolated through the Repository and Data Mapper patterns.

Repositories will expose domain-oriented interfaces.

Data Mappers will translate between persistence models and pure domain objects.

The domain layer will contain no persistence-specific code.

---

## Consequences

### Positive

- Domain objects remain persistence ignorant.
- Database technology can evolve independently.
- Domain tests require no database.
- Persistence concerns remain isolated.

### Negative

- Mapping logic must be maintained.
- Slightly more implementation complexity.
