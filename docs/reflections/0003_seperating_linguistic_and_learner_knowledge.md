# Reflection 0003: Separating Linguistic Knowledge From Learner Knowledge

**Feature Branch:** `docs/product-vision`

## Context

While defining the product vision for the Chinese learning platform, the original domain model was reviewed against the intended learning workflows.

The initial model focused primarily on analysing Chinese text:

- Character
- Token
- Sentence
- Comprehensibility Score

However, when considering the actual user workflows, it became clear that the system is not primarily a text analysis system. It is a learning platform where analysed language content is used to create personalised learning experiences.

The distinction between linguistic information and learner knowledge became a key domain discovery.

---

## Initial Assumption

The initial assumption was that concepts such as comprehensibility could naturally belong to the Sentence aggregate.

For example:

```text
Sentence
    |
    +-- ComprehensibilityScore
```

This implied that a sentence had an inherent difficulty or readability.

---

## Problem Discovered

A sentence does not have a fixed level of difficulty.

The difficulty depends on:

- The learner's existing vocabulary
- The learner's character recognition ability
- The learner's grammar knowledge
- Previous exposure to similar structures

The same sentence may be:

- Easy for one learner
- Difficult for another learner

Therefore, difficulty and comprehensibility are not intrinsic properties of the sentence itself.

---

## Domain Insight

The system contains two separate types of knowledge.

### Linguistic Knowledge

Information about Chinese itself.

Examples:

- Character: 天
- Token: 今天
- Sentence: 我今天学习中文

This information exists independently of any learner.

---

### Learner Knowledge

Information about what a specific learner knows.

Examples:

- Learner recognises the character 天
- Learner knows 今天 means today
- Learner has not learned 天空

This information belongs to the learner.

---

## Decision

The domain model will separate linguistic concepts from learner state.

The relationship becomes:

```text
Chinese Language Model

Character
Token
Sentence
        +

Learner Model

CharacterKnowledge
VocabularyKnowledge
GrammarKnowledge

        |

        v

Learning Analysis

ComprehensibilityScore
ReadingDifficulty
ProgressMetrics
```

---

## Character Recognition vs Vocabulary Knowledge

A further distinction was identified between recognising characters and knowing vocabulary.

A learner may:

- recognise 天 visually
- pronounce 天 correctly
- know 今天 means today
- not know 天 means sky

Therefore:

Character recognition and vocabulary knowledge should be tracked separately.

Example:

```text
Character Knowledge:

天
Recognised: true


Vocabulary Knowledge:

今天
Known: true

天空
Known: false
```

---

## Impact on Roadmap

The original placement of `ComprehensibilityScore` in the core domain was reconsidered.

Instead of being implemented as a foundational concept, it will be introduced after learner knowledge exists.

Updated dependency:

```text
Character
Token
Sentence

        |

Learner Knowledge

        |

Comprehensibility Analysis
```

---

## Future Implications

This decision allows the platform to support multiple learning activities:

- Vocabulary recall
- Character recognition
- Reading practice
- AI conversation
- Sentence construction

without forcing all learning outcomes into the Sentence model.

A sentence becomes reusable learning content rather than the owner of learning state.

---

## Conclusion

The product vision clarified that the core domain is not simply Chinese text analysis.

The core domain is the interaction between:

- Chinese language content
- Learner knowledge
- Learning activities

Future development should preserve this separation.
