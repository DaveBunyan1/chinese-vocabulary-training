# ADR-0004: Use Domain Events for Analytics and Observability

## Status

Accepted

---

## Context

The platform derives learner progress, adaptive review scheduling, and
analytics from business activity.

Previous experience showed that introducing telemetry after implementing core
application workflows makes observability significantly harder.

The system also requires historical business events for future analytics.

---

## Decision

Important business actions will emit Domain Events.

Examples include:

- RecallAttemptRecorded
- VocabularyLearned
- PracticeSessionCompleted
- SentenceAnalysed
- ConversationCompleted

These events may be consumed by multiple independent components including:

- Analytics
- Logging
- Telemetry
- Notifications
- Future integrations

The domain itself will not depend on any telemetry framework.

---

## Consequences

### Positive

- Analytics are derived naturally from business activity.
- Telemetry can evolve independently.
- New consumers can subscribe without changing domain logic.
- Better separation of concerns.

### Negative

- Event infrastructure introduces additional complexity.
- Event versioning may become necessary as the system evolves.
