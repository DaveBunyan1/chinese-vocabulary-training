# Domain Model

## Chinese Learning Platform

---

# 1. Purpose

The Chinese Practice Application enables learners to improve reading comprehension, vocabulary retention, and conversational fluency through adaptive practice, sentence analysis, and AI-assisted conversations.

The core business problem is

> How can we continuously adapt learning material to a learner's current knowledge while maximising long-term vocabulary retention?

This document describes the business domain only. It intentionally contains no implementation details and is independent of any UI framework, database, machine learning model, NLP library, or external service.

---

# 2. Ubiquitous Language

| Term                    | Definition                                                                          |
| ----------------------- | ----------------------------------------------------------------------------------- |
| Learner                 | A person using the platform to study Chinese.                                       |
| Character               | A single Chinese logographic character.                                             |
| Token                   | A meaningful linguistic unit consisting of one or more Characters.                  |
| Sentence                | An ordered collection of Tokens representing a complete thought.                    |
| Vocabulary Item         | A Character or Token tracked by the learning system.                                |
| Pinyin                  | The contextual pronunciation of a Character or Token.                               |
| Word Status             | The learner's familiarity with a Vocabulary Item (New, Learning, Known).            |
| User Vocabulary Profile | The complete collection of Vocabulary Items belonging to a Learner.                 |
| Practice Session        | A collection of exercises completed by a Learner.                                   |
| Reading Passage         | One or more Sentences presented for reading practice.                               |
| Recall Attempt          | A single attempt to recognise or translate a Vocabulary Item.                       |
| Recall Weight           | A calculated priority indicating how urgently a Vocabulary Item should be reviewed. |
| Comprehensibility Score | The percentage of Tokens within a Sentence recognised by the Learner.               |
| Prompt Context          | Vocabulary extracted from a Learner's Vocabulary Profile for AI conversations.      |
| Tag                     | A hierarchical classification applied to learning material.                         |

---

# 3. Core Domain

```
Chinese Learning Domain

├── Learner
│
├── Vocabulary
│   ├── UserVocabularyProfile
│   ├── VocabularyItem
│   └── WordStatus
│
├── Text Analysis
│   ├── Sentence
│   ├── Token
│   └── Character
│
├── Practice
│   ├── PracticeSession
│   ├── ReadingPassage
│   └── ReviewQueue
│
├── Analytics
│   ├── RecallAttempt
│   ├── RetentionStatistics
│   ├── LearningStatistics
│   ├── ProgressSnapshot
│   ├── RecallWeight
│   ├── LearningTrend
│   └── CategoryPerformance
│
├── Conversation
│   ├── ChatSession
│   └── PromptContext
└── LearningProgress
    │
    ├── Vocabulary Growth
    ├── Reading Level
    ├── Retention Statistics
    ├── Learning Trends
    └── Category Performance
```

---

# 4. Aggregates

## Learner (Aggregate Root)

Represents a learner using the platform.

### Responsibilities

- Owns a UserVocabularyProfile.
- Owns PracticeSessions.
- Owns ChatSessions.
- Owns Recall history.
- Tracks overall learning progress.

### Invariants

- Every UserVocabularyProfile belongs to exactly one Learner.
- PracticeSessions cannot be shared between Learners.
- A Learner cannot own duplicate Vocabulary Profiles.

---

## Sentence (Aggregate Root)

Represents a complete sentence.

### Responsibilities

- Maintains an ordered collection of Tokens.
- Calculates Comprehensibility Score.
- Produces immutable sentence variations.
- Maintains sentence metadata.

### Invariants

- A Sentence must contain at least one Token.
- Token ordering is preserved.
- Tokens cannot be null.

---

## UserVocabularyProfile (Aggregate Root)

Represents everything known about a learner's vocabulary.

### Responsibilities

- Tracks vocabulary knowledge.
- Promotes Vocabulary Items between learning stages.
- Exposes known vocabulary for downstream services.
- Records vocabulary statistics.

### Invariants

- Duplicate Vocabulary Items are not permitted.
- Every Vocabulary Item has exactly one status.

---

## PracticeSession (Aggregate Root)

Represents one revision or learning session.

### Responsibilities

- Records completed exercises.
- Stores performance statistics.
- Produces learning summaries.

### Invariants

- Completed sessions are immutable.
- All recorded attempts belong to the owning Learner.

## LearningProgress (Aggregate Root)

### Responsibilities

- Tracks overall learner progress.
- Produces summary statistics.
- Calculates reading level.
- Tracks HSK progression.
- Tracks vocabulary growth.
- Tracks learning streaks.

---

# 5. Entities

## VocabularyItem

Represents one tracked word or phrase.

### Properties

- identifier
- text
- pinyin
- part of speech

---

## RecallAttempt

Represents one immutable learning event.

### Properties

- timestamp
- vocabulary item
- success
- response time

---

## ChatSession

Represents one AI conversation.

### Properties

- conversation history
- extracted vocabulary
- prompt context

---

## ReadingPassage

Represents a collection of Sentences used for reading practice.

### Properties

- title
- sentences
- tags
- estimated difficulty

---

# 6. Value Objects

## Character

Contains

- character
- radical
- stroke count

Immutable.

---

## Token

Contains

- text
- pinyin
- part of speech

Immutable.

---

## RecallWeight

Represents review priority.

Immutable.

---

## ComprehensibilityScore

Represents sentence readability.

Immutable.

---

## WordStatus

Represents the learner's current familiarity.

Possible values

- New
- Learning
- Known

Immutable.

---

# 7. Domain Services

## SentenceAnalysisService

Transforms raw Chinese text into domain objects.

### Responsibilities

- Segment text into Tokens.
- Resolve contextual Pinyin.
- Determine part of speech.
- Build Sentence aggregates.

---

## SentenceMutationService

Produces alternative sentences while preserving grammatical correctness.

---

## RecallWeightCalculator

Calculates review priority.

Policy

$$
Weight = \frac{Total Attempts}{Successful Attempts + 1} × Days Since Last Review
$$

---

## ReviewQueueService

Produces prioritised review material.

### Responsibilities

- Apply recall weights.
- Filter by Tags.
- Randomise equally weighted items.

---

## PromptContextBuilder

Constructs conversational vocabulary constraints from the Learner's known vocabulary.

---

## LearningAnalyticsService

### Responsibilities

Calculate

- Vocabulary growth
- Reading comprehension
- Retention statistics
- Category performance
- Practice efficiency
- Daily activity
- Weekly trends
- Reading level progression

---

# 8. Learning Metrics

The platform continuously derives learning metrics from historical learner activity. These metrics are projections computed from PracticeSessions, RecallAttempts, ChatSessions, and the UserVocabularyProfile.

Learning metrics provide insight into learner progress and support adaptive content selection, personalised revision, and progress reporting.

## Core Metrics

| Metric                | Description                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------ |
| Vocabulary Growth     | Number of Vocabulary Items acquired over time.                                             |
| Reading Comprehension | Percentage of Tokens recognised within reading passages.                                   |
| Recall Accuracy       | Success rate across historical RecallAttempts.                                             |
| Category Retention    | Retention statistics grouped by hierarchical Tags.                                         |
| Learning Velocity     | Rate of vocabulary acquisition over time.                                                  |
| Practice Consistency  | Frequency and regularity of completed PracticeSessions.                                    |
| Reading Level         | Estimated reading ability derived from comprehensibility metrics.                          |
| Daily Learning Streak | Consecutive days with completed learning activity.                                         |
| HSK Progression       | Represents the proportion of known words compared to the tracked words for a certain level |

These metrics are read models derived from domain events rather than primary domain entities.

---

# 9. Domain Policies

## Vocabulary Progression

Vocabulary progresses through the following stages:

New

↓

Learning

↓

Known

Promotion occurs only when configured mastery conditions are satisfied.

---

## Adaptive Review

Vocabulary with lower historical retention receives greater review priority.

Recently reviewed material receives lower priority.

---

## Sentence Mutation

Mutated sentences must

- remain grammatically valid
- preserve sentence meaning where possible
- never modify the original Sentence

---

## AI Conversations

AI responses should

- primarily use Known vocabulary
- introduce a limited amount of new vocabulary
- expose new words in meaningful context

---

# 10. Domain Events

`VocabularyItemLearned`

Raised when a Vocabulary Item becomes Known.

---

`RecallAttemptRecorded`

Raised whenever a learner completes a review attempt.

---

`PracticeSessionCompleted`

Raised when a learning session finishes.

---

`SentenceMutated`

Raised after successful sentence substitution.

---

`ConversationCompleted`

Raised when an AI conversation ends.

---

# 11. Future Extensions

The domain model has been designed to support future capabilities without
changing the core model.

Potential extensions include

- Speech recognition
- Pronunciation assessment
- Tone accuracy analysis
- Handwriting recognition
- Grammar correction
- Adaptive reading recommendations
- Personalised lesson generation
- Multi-language support

---

# 12. Out of Scope

The following concerns are intentionally excluded from this domain model:

- Authentication
- Password management
- Email verification
- OAuth providers
- User interface implementation
- Database persistence
- NLP implementation details
- LLM provider integration
- API design
- Infrastructure and deployment
