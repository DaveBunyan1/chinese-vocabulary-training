# ADR-005: Introduce VocabularyItem as a Canonical Linguistic Entity

**Status:** Accepted

**Date:** 2026-07-23

**Feature Branch**: `feat/domain-vocabulary-item`

## Context

The platform stores Chinese language content which is later used for multiple
learning activities, including:

- Vocabulary recall
- Character recognition
- Reading practice
- AI conversation
- Sentence construction

Initially, it was unclear whether a `Token` should also represent a vocabulary
entry or whether learner-specific information should be stored alongside
language data.

During development of the product vision, a distinction emerged between:

- language that exists independently of any learner
- knowledge possessed by an individual learner

This required introducing a dedicated model representing canonical vocabulary.

---

## Decision

Introduce a `VocabularyItem` domain entity.

A `VocabularyItem` represents a Chinese word or phrase independent of any
learner.

A vocabulary item contains linguistic information such as:

- identifier
- Chinese text
- pinyin
- English meaning
- part of speech (where available)

It does **not** contain:

- learner familiarity
- learning status
- recall statistics
- practice history
- category progress

These belong to learner-specific aggregates.

---

## Relationships

The language model becomes:

```text
Sentence
    |
    +-- Token
            |
            +-- VocabularyItem

Character
```

A `Token` represents an occurrence of text within a sentence.

A `VocabularyItem` represents the canonical linguistic concept referenced by
that token.

Characters remain independent linguistic units.

---

## Consequences

### Advantages

- Separates language data from learner data.
- Allows multiple tokens to reference the same vocabulary item.
- Supports multiple learning activities using the same vocabulary model.
- Prevents learner state leaking into the language domain.
- Keeps the linguistic model reusable and immutable.

### Trade-offs

- Introduces another domain concept.
- Requires an analysis step to associate tokens with vocabulary items.
- Vocabulary lookup becomes an explicit responsibility of the application layer
  rather than the Token itself.

---

## Future Work

Future branches will introduce:

- Learner vocabulary knowledge
- Character knowledge
- Vocabulary recall history
- Reading analytics

These concepts will reference `VocabularyItem` rather than extending it with
learner-specific state.
