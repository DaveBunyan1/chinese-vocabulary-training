# ADR-0006: Prioritise Observability from Project Inception

## Status

Accepted

---

## Context

The Chinese Learning Platform is intended to evolve over time, incorporating
new language processing capabilities, adaptive learning strategies, AI
providers, and analytics.

Previous experience demonstrated that introducing observability after core
application workflows have been implemented significantly increases the effort
required to understand system behaviour and diagnose issues.

Retrofitting logging, metrics, tracing, and telemetry often requires invasive
changes across multiple layers of the application and provides only partial
visibility into historical architectural decisions.

Observability should therefore be considered a foundational architectural
concern rather than an operational feature.

---

## Decision

The project will incorporate observability from the beginning of development.

The architecture will ensure that significant business and application events
can be observed without coupling business logic to any specific telemetry
framework.

Observability will be introduced incrementally and may include:

- Structured logging
- Metrics
- Distributed tracing
- Health checks
- Application diagnostics
- Build and deployment reporting

Continuous Integration pipelines will automatically validate the health of the
codebase by executing:

- Static analysis
- Formatting checks
- Type checking
- Unit tests
- Integration tests
- Coverage reporting

Observability tooling will remain part of the infrastructure layer and must not
introduce dependencies into the domain model.

---

## Consequences

### Positive

- System behaviour can be understood from the earliest stages of development.
- Architectural regressions become easier to detect.
- Performance bottlenecks can be identified before they become significant.
- New infrastructure can be monitored without modifying business logic.
- Continuous Integration provides rapid feedback on code quality.
- Operational concerns remain separate from the domain model.

### Negative

- Additional development effort is required before user-facing features are
  implemented.
- Early project complexity increases.
- Some observability infrastructure may initially provide limited practical
  value until more functionality has been implemented.

---

## Notes

This decision was influenced by lessons learned from previous projects where
observability and telemetry were introduced after substantial application
logic had already been developed.

Establishing observability as a foundational capability aims to reduce future
technical debt and improve confidence when evolving the system.

This ADR intentionally does not prescribe specific technologies.

Technology choices (for example, logging libraries, telemetry frameworks, or
CI platforms) will be documented separately if and when those decisions are
made.
