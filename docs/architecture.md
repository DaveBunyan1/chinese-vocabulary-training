# Architecture Document

## Chinese Learning Platform

---

# 1. Purpose

This document describes the architectural design of the Chinese Learning Platform.

The architecture is designed around the following goals:

- Maintain a pure and testable domain model.
- Separate business rules from technical concerns.
- Allow independent evolution of NLP, AI, persistence, and presentation layers.
- Support analytics and adaptive learning from the beginning.
- Enable observability without coupling telemetry to business logic.

This project uses Domain-Driven Design to model the Chinese learning domain and applies Ports and Adapters (also known as Hexagonal Architecture) to isolate the domain from infrastructure concerns.

This approach has the following ideas:

- Business rules are isolated from infrastructure concerns.
- Dependencies point toward the domain.
- External systems communicate through explicit interfaces.

---

# 2. Architectural Principles

## Domain First

The business domain is the centre of the system.

The domain model should be understandable without knowledge of:

- Database technology
- Web frameworks
- AI providers
- NLP libraries
- User interface technologies

The domain defines:

- Business concepts
- Business rules
- Domain events
- Invariants

---

## Dependency Direction

Dependencies must always point inward.

```
                    Presentation

                         |
                         v

                  Application Layer

                         |
                         v

                    Domain Layer


                         ^
                         |

                Infrastructure Layer
```

The domain layer has no dependency on external systems.

---

## Replaceable Infrastructure

External technologies should be replaceable without changing business logic.

**Examples:**

- NLP engine can change.
- LLM provider can change.
- Database technology can change.
- API framework can change.

---

# 3. High-Level Architecture

```
+------------------------------------------------+
|                 Presentation                   |
|                                                |
| REST API                                       |
| Web Interface                                  |
| CLI                                            |
+-------------------------+----------------------+
                          |
                          v
+------------------------------------------------+
|                Application                     |
|                                                |
| Use Cases                                      |
| Application Services                           |
| Command Handling                               |
+-------------------------+----------------------+
                          |
                          v
+------------------------------------------------+
|                  Domain                        |
|                                                |
| Learner                                        |
| Vocabulary                                     |
| Sentence                                       |
| Practice                                       |
| Analytics                                      |
| Conversation                                   |
+-------------------------+----------------------+
                          ^
                          |
+------------------------------------------------+
|               Infrastructure                   |
|                                                |
| Database                                       |
| NLP Providers                                  |
| LLM Providers                                  |
| Telemetry                                      |
| External Services                              |
+------------------------------------------------+
```

---

# 4. Domain Layer

The domain layer contains the core business logic.

**Location:**

```
src/domain/
```

**Responsibilities:**

- Define aggregates.
- Enforce business invariants.
- Calculate domain values.
- Emit domain events.

The domain layer contains no:

- Database models.
- HTTP code.
- API schemas.
- Framework dependencies.

---

## Domain Components

```
domain/

├── learner
│
├── vocabulary
│
├── text_analysis
│
├── practice
│
├── analytics
│
└── conversation
```

---

# 5. Application Layer

The application layer coordinates domain behavior and executes user-facing workflows.

**Location:**

```
src/application/
```

**Responsibilities:**

- Execute application use cases using a Pragmatic CQRS approach (Commands vs. Queries).
- Orchestrate aggregates and domain services for write operations.
- Execute fast, projection-based read queries for presentation models without instantiating heavy domain aggregates.
- Manage database transaction boundaries.
- Publish domain events triggered by state mutations.
- Depend solely on abstract ports (interfaces), never concrete infrastructure.

The application layer contains zero business rules or invariants; it acts as a conductor.

## Architectural Command/Query Separation

```text
                        Presentation / API
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
     [ Command Handler ]                   [ Query Handler ]
             |                                     |
             v                                     v
    Domain Aggregates                     Raw DTO Projections
   (Write / Invariants)                  (Fast Read Models)
             |                                     |
             v                                     v
    Repository Ports                      Read Database / Views
```

---

## Example Use Cases

### Command Handlers (Mutations via Domain Aggregates)

`AnalyseSentenceCommand`

- **Input:** Raw Chinese text, Learner ID
- **Process:**
  1. Call `SentenceAnalysisService` (NLP port) to tokenize and resolve pinyin.
  2. Instantiate `Sentence` aggregate.
  3. Load `UserVocabularyProfile` via repository.
  4. Calculate comprehensibility score.
  5. Persist via `SentenceRepository`.
- **Output:** Aggregate ID / Status DTO

`RecordRecallAttemptCommand`

- **Input:** Learner ID, Target Item ID, Item Type (Character/Phrase), `was_correct` (bool)
- **Process:**
  1. Fetch `UserVocabularyProfile` aggregate.
  2. Invoke `record_attempt()` domain method.
  3. Emit `RecallAttemptRecorded` domain event.
  4. Save updated aggregate state via repository.
- **Output:** Updated recall status summary

### Query Handlers (Read Projections / Read DTOs)

`GetSentenceForReaderQuery`

- **Input:** Sentence ID, Learner ID
- **Process:**
  - Execute an optimized, direct SQL join (via Infrastructure Read Service) combining raw text, pre-calculated pinyin, category tags, and user word retention status into a flat projection DTO.
  - Bypasses aggregate hydration for maximum UI rendering performance.
- **Output:** `InteractiveReaderDTO` (UI-ready JSON shape)

---

# 6. Infrastructure Layer

The infrastructure layer provides technical implementations.

**Location:**

```
src/infrastructure/
```

Responsibilities:

- Persistence.
- External API communication.
- NLP integration.
- AI integration.
- Observability.

---

## Infrastructure Adapters

**Examples:**

```
infrastructure/

├── persistence
│
│   Repository implementations
│
├── nlp
│
│   Tokenization adapters
│   Pinyin resolution
│
├── llm
│
│   AI provider adapters
│
├── telemetry
│
│   Logging
│   Metrics
│   Tracing
│
└── configuration
```

---

# 7. Repository Pattern

The domain should not know how data is stored.

Repositories provide an abstraction between the domain and persistence.

**Example:**

```
Application Service

        |
        v

VocabularyRepository Interface

        |
        v

SQL Repository Implementation
```

The domain depends on abstractions, not databases.

---

# 8. Domain Events and Observability

Important business events are first-class concepts.

**Examples:**

```
VocabularyLearned

RecallAttemptRecorded

PracticeSessionCompleted

SentenceAnalysed

ConversationCompleted
```

Events may be consumed by:

```
                Domain Event

                     |
        +------------+------------+
        |            |            |
        v            v            v

    Analytics   Telemetry   Notifications
```

Telemetry observes the system without becoming part of business logic.

---

# 9. Analytics Architecture

Analytics in this platform are treated as read-side projections derived from historical domain activity, rather than monolithic core entities.

Primary domain events emitted by the system:

```
RecallAttemptRecorded

PracticeSessionCompleted

VocabularyStatusChanged
```

## Event-Driven Analytics Flow

```text
[ Domain Mutation ]
          |
          v
  Domain Event Emitted (e.g., RecallAttemptRecorded)
          |
          +-------------------+-------------------+
          |                                       |
          v                                       v
[ Primary Write Store ]                [ Analytics Projection ]
 (UserVocabularyProfile)               (Event Log / Read Tables)
                                                  |
                                                  v
                                       Calculated Retention Metrics
                                       (HSK Level, Category Decay,
                                        Weighted Review Queues)
```

## Analytics Capabilities

The analytics pipeline projects historical event data to generate:

- **Category & Subcategory Retention Rates:** Performance broken down by taxonomy nodes (e.g., `HSK > HSK1` vs. `Topic > Food`).
- **Category & Subcategory Retention Rates:** Performance broken down by taxonomy nodes (e.g., HSK > HSK1 vs. Topic > Food).
- **Vocabulary Velocity:** Growth trends over time across characters and multi-character phrases.
- **Comprehensibility Projections:** Predicted reading accuracy across untried sentences based on current known vocabulary.

---

# 10. NLP Architecture

Natural language processing is isolated behind interfaces.

The domain knows:

```
SentenceAnalysisService
```

It does not know:

```
jieba
spaCy
transformers
```

Possible implementations can change without affecting the domain.

Example:

```
SentenceAnalysisService Interface

              |
              |

      NLP Adapter Implementation

              |
              |

        External NLP Library
```

---

# 11. AI Conversation Architecture

The AI system is treated as an external capability.

The domain owns:

- Conversation concepts.
- Vocabulary constraints.
- Learning goals.

The infrastructure owns:

- LLM communication.
- Prompt transport.
- API authentication.

Example:

```
Learner

   |
   v

PromptContextBuilder

   |
   v

LLM Adapter

   |
   v

External AI Provider
```

---

# 12. Testing Strategy

Testing follows architectural boundaries to maximize suite velocity and maintain high domain confidence.

```text
+-----------------------+
                     |     End-to-End        |   (Slowest / Fewest)
                     +-----------------------+
                     |  Infrastructure Tests |
                     +-----------------------+
                     |   Application Tests   |
                     +-----------------------+
                     |     Domain Tests      |   (Fastest / Most)
                     +-----------------------+
```

## esting Boundaries

### 1. Domain Tests (Highest Priority)

- **Focus:** Pure unit tests covering Aggregates, Value Objects, Domain Services, and Invariant Rules.
- **Speed:** Runs in microseconds.
- **Dependencies:** Zero infrastructure, zero databases, zero external libraries.

### 2. Application Tests

- **Focus:** Testing use-case orchestration, command handling, and query projections.
- **Adapter Strategy:** Every Repository interface defined in the application layer must provide a lightweight In-Memory implementation (e.g., InMemorySentenceRepository) alongside its SQL counterpart.
- **Benefit:** Tests execute complete application workflows instantly without spinning up a database or managing real network connections.

### 3. Infrastructure Tests

- **Focus:** Verifying that concrete adapters correctly interact with external systems.
- **Coverage:**
  - Database adapters verse an actual test database.
  - NLP adapter tests verifying parsing output.
  - LLM provider communication tests using recorded HTTP fixtures

### 4. End-to-End (E2E) Tests

- Focus: Validating critical user journeys from the presentation layer down to the storage layers.
- Execution: Run inside CI pipelines before deployment gates.

---

# 13. Development Infrastructure

The project will include:

## Continuous Integration

Every change should automatically run:

```
Linting

Type checking

Unit tests

Integration tests

Coverage checks

Build verification
```

---

## Code Quality

Standards:

- Automated formatting.
- Static type checking.
- Automated testing.
- Consistent code style.

---

## Local Development

Development environments should be reproducible through:

- Containerisation.
- Environment configuration.
- Automated setup scripts.

---

# 14. Architectural Evolution & Retrospective

The design of this platform is directly informed by architectural friction and technical debt encountered during the development of a real-time audio processing application (Violin Practice App).

---

## 1. Concrete Domain Boundaries Before Technical Spikes

### Lesson Learned

In the violin app, development began with exploratory hardware spikes (e.g., using `sounddevice` and signal processing libraries to capture microphone input). Because no domain model was established upfront, infrastructure code (audio stream handling) became tightly coupled to core application rules (pitch evaluation and practice routines). Refactoring later required untangling hardware logic from business logic at significant time cost.

### Architectural Decision

Domain entities, aggregates, and interfaces are defined **first**, using pure Python without external dependencies. Technical spikes (e.g., testing NLP tokenization with `jieba` or LLM streaming APIs) are isolated strictly inside adapter modules in the `infrastructure/` layer.

---

## 2. Test-Driven Development (TDD) as a Pre-requisite to Refactoring

### Lesson Learned

Testing in the previous project was introduced late in the development cycle. As core requirements evolved and frequent refactoring was needed, maintaining retrofitted tests became brittle and burdensome, ultimately leading to low test coverage and fragile builds.

### Architectural Decision

Strict TDD is enforced for all core domain logic from Day 1. By isolating the domain layer behind explicit Repository ports and providing fast In-Memory implementations (`InMemorySentenceRepository`), the test suite executes in milliseconds, encouraging continuous refactoring without fear of regressions.

## 3. Early Observability and Telemetry Setup

### Lesson Learned

Attempting to trace pitch detection accuracy and pipeline performance without structured logging or metrics made debugging audio processing bottlenecks extremely difficult after the pipeline was already assembled, alongside making architectural changes without knowing the impact it had on performance.

### Architectural Decision

Structured logging (`Structlog`) and tracing primitives (`OpenTelemetry`) are baked into the application and infrastructure layers from the very first use-case implementation, ensuring complete visibility into sentence parsing and AI latency from day one.

### 4. Explicit Dependency Injection over Global Singletons

- **Lesson Learned:** Instantiating database handles, configuration objects, and state stores as module-level global singletons created fragile circular import loops (`Module A ↔ Module B`). Untangling these dependencies required runtime workarounds that severely slowed down developer velocity and made isolated unit testing nearly impossible.
- **Architectural Decision:** Global singletons are strictly forbidden. All infrastructure dependencies, repositories, and services are constructed at the application entry point (`main.py`) and passed inward using explicit **Constructor Injection** (`__init__`). We deliberately accept the nanosecond overhead of object passing in exchange for a clean runtime dependency graph, zero circular imports, and frictionless unit testing.

---

# 15. Future Architectural Evolution

Potential future additions:

- Distributed analytics pipeline.
- Background learning recommendation workers.
- Offline learning mode.
- Multiple language support.

The architecture should allow these capabilities without changing the core
domain model.
