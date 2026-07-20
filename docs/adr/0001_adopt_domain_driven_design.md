# ADR-0001: Adopt Domain-Driven Design

## Status

Accepted

---

## Context

The Chinese Learning Platform models a rich business domain centred around
language acquisition, vocabulary retention, adaptive practice, and AI-assisted
conversation.

The application contains complex business concepts including Learners,
Vocabulary Profiles, Practice Sessions, Recall Attempts, and Learning
Analytics.

Without a shared domain model, business logic would become distributed across
controllers, persistence models, and infrastructure, making the system harder
to understand and evolve.

---

## Decision

The project will adopt Domain-Driven Design (DDD) as its primary modelling
approach.

Business concepts will be represented using:

- Ubiquitous Language
- Entities
- Value Objects
- Aggregates
- Domain Services
- Domain Events
- Bounded Contexts

The domain model will remain independent of infrastructure concerns.

---

## Consequences

### Positive

- Business concepts remain explicit.
- Rich domain behaviour can be tested independently.
- Common vocabulary is shared throughout the project.
- Business rules remain isolated from infrastructure.

### Negative

- More initial design work is required.
- Additional abstraction compared to CRUD-based architectures.
