# ADR-0002: Adopt Ports and Adapters Architecture

## Status

Accepted

---

## Context

The application depends upon several external technologies, including:

- Persistence
- NLP processing
- AI providers
- Telemetry
- Web APIs

These technologies are expected to evolve independently throughout the life of
the project.

Previous projects demonstrated that tightly coupling business logic to
frameworks and external services increases maintenance cost and makes
experimentation more difficult.

---

## Decision

The project will adopt the Ports and Adapters (Hexagonal Architecture)
approach.

Business logic will depend only upon abstractions.

Infrastructure components will implement those abstractions as adapters.

Dependencies will always point toward the domain.

---

## Consequences

### Positive

- Infrastructure can be replaced independently.
- Domain logic remains framework independent.
- Unit testing becomes significantly easier.
- New technologies can be introduced with minimal impact.

### Negative

- Additional interfaces increase the amount of boilerplate.
- More architectural discipline is required.
