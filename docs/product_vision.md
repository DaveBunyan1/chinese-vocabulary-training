# Product Vision

## 1. Overview

This project is a Chinese language learning platform designed to help learners
develop reading, vocabulary recall, conversational ability, and sentence
construction skills through personalised practice.

The system combines:

- Chinese text analysis
- Vocabulary tracking
- Learner progress modelling
- Practice generation
- AI-assisted conversation
- Automated feedback

The core principle is that learning should be based on the learner's current
knowledge, allowing practice material and feedback to adapt over time.

---

# 2. Goals

## Primary Goals

The system should allow a learner to:

- Build and maintain a personal vocabulary profile.
- Practice recognition and recall of Chinese vocabulary.
- Analyse and study authentic Chinese text.
- Understand their current reading ability.
- Practise producing grammatically correct Chinese sentences.
- Have conversations using vocabulary appropriate to their level.
- Track progress over time.

---

# 3. Core Learning Activities

The system supports four primary learning activities.

---

# 3.1 Vocabulary Recall Practice

## Purpose

Test whether a learner can recall vocabulary items in different forms.

## Supported Exercise Types

The system should support exercises including:

### Chinese → English

Example:

Question:

```text
天气
```

Answer:

```text
weather
```

---

### Chinese → Pinyin

Example:

Question:

```text
学习
```

Answer:

```text
xué xí
```

---

### Pinyin → English

Example:

Question:

```text
tiān qì
```

Answer:

```text
weather
```

---

### English → Chinese

Example:

Question:

```text
weather
```

Answer:

```text
天气
```

---

### English → Pinyin

Example:

Question:

```text
to learn
```

Answer:
xué xí

---

## Exercise Configuration

Exercises can be generated from:

- Specific categories
  - HSK level
  - topic categories (food, travel, etc.)
  - user-defined categories

- Learner knowledge scope:
  - all known vocabulary
  - vocabulary within selected categories

Exercises may contain:

- Individual vocabulary tokens
- Sentences
- A mixture of both

---

## Scoring

Vocabulary recall is scored using binary correctness.

An answer is either:

- Correct
- Incorrect

Example:

```text
Exercise:
5 questions

Results:
4 correct
1 incorrect
```

The system should preserve individual results rather than only storing an
aggregate percentage.

Each successful or unsuccessful attempt updates the learning history of the
specific vocabulary item or sentence.

---

# 3.2 Reading and Character Recognition Practice

## Purpose

Allow learners to practise recognising Chinese text and connecting characters
with pronunciation and meaning.

---

## Input

The learner can provide authentic Chinese text.

Example:

```text
铁柱坐在村内的小路边，望着蔚蓝的天空，神情发呆，铁柱不是他的本名，
而是从小因为身体瘦弱，父亲怕养不活，于是按照习俗称呼的小名。
```

The system analyses and stores:

- Sentences
- Tokens
- Characters
- Pinyin
- Vocabulary relationships
- Meaning information

---

## Practice Modes

The learner can practise:

### Character Recognition

The system displays Chinese text.

The learner selects characters they recognise.

Example:

```text
铁 ✓
柱 ?
坐 ✓
在 ✓
村 ?
内 ✓
```

The learner enters pinyin for recognised characters.

The system compares:

- Characters marked as known
- Correct pinyin
- Existing learner knowledge

---

## Results

The system provides:

### Overall sentence performance

Example:

```text
Sentence recognition:
64% of characters recognised
```

---

### Individual character performance

Example:

```text
铁
Recognised: Yes
Pinyin: tiě
Previous knowledge: Known

柱
Recognised: No
Pinyin: zhù
Previous knowledge: Learning
```

---

## Purpose of Sentence-Level Scoring

Sentence-level scores should represent the learner's ability to process that
specific sentence.

A learner may recognise a character in one context but not another word.

Example:

The learner may recognise:

```text
今天
昨天
```

but not:

```text
蓝天
```

Therefore recognition should support context-dependent learning.

---

# 3.3 AI Conversation Practice

## Purpose

Allow learners to practise conversational Chinese with AI assistance.

---

## Conversation Generation

The system generates conversations using:

- Learner vocabulary knowledge
- Selected categories
- Target grammar structures
- Desired difficulty level

The AI should construct sentences that are:

- Grammatically correct
- Natural Chinese
- Appropriate for the learner's level

---

## Example

The system may ask:

```text
你昨天晚上几点睡觉？
```

The learner responds:

```text
我昨天晚上十一点睡觉。
```

The system evaluates:

- Vocabulary usage
- Grammar correctness
- Sentence meaning
- Appropriateness of response

---

# 3.4 Sentence Construction Practice

## Purpose

Teach learners to produce Chinese sentences using existing grammatical patterns.

---

## Exercise Format

The system provides a sentence pattern.

Example:

```text
昨天晚上我十点睡觉。
```

The learner creates a new sentence using the same structure.

Example:

```text
今天下午我看电影。
```

---

## Evaluation

The response should be evaluated on:

- Grammar structure
- Word order
- Vocabulary correctness
- Character correctness
- Intended meaning

---

# 4. Content Management

## Adding Chinese Text

A learner can add new Chinese content.

Input:

- Chinese text
- Translation / meaning
- Optional category tags

The system analyses the content and extracts:

- Sentences
- Tokens
- Characters
- Vocabulary relationships
- Pronunciation information

---

# 5. Vocabulary Knowledge Model

The system maintains a profile of learner knowledge.

Vocabulary can have states such as:

- New
- Learning
- Known

The learner profile tracks:

- Vocabulary familiarity
- Recall history
- Practice performance
- Reading exposure

---

# 6. Categories and Filtering

Vocabulary and learning material can be organised by:

- HSK level
- Topic
- User-created categories
- Difficulty

Categories can be used for:

- Practice generation
- AI conversation constraints
- Reading material filtering

---

# 7. Analytics and Progress Tracking

The system should provide learning analytics including:

- Vocabulary growth
- Recall performance
- Reading ability progression
- Practice history
- Retention statistics
- Category performance
- Learning trends

Analytics should be calculated from learning events rather than stored as
manually updated values.

---

# 8. MVP Scope

## MVP Phase 1: Vocabulary Recall

Support:

- Vocabulary items
- Categories
- Multiple-choice recall
- Answer attempts
- Scoring history

Domain:

```text
VocabularyItem
VocabularyKnowledge
Exercise
Question
AnswerAttempt
```

---

## MVP Phase 2: Character Recognition

Support:

Input:

```text
Chinese sentence
```

System extracts:

```text
Sentence
 |
 Characters
```

Practice:

```text
Select known characters
Enter pinyin
```

System records:

```text
CharacterRecognitionAttempt
```

Domain:

```text
Character
CharacterKnowledge
CharacterAttempt
ReadingExercise
```

---

## MVP Phase 3: Reading Comprehension

Combine:

```text
CharacterKnowledge
VocabularyKnowledge
GrammarKnowledge
```

into:

```text
ComprehensibilityAnalysis
```

---

## Future Extensions

Potential future features:

- AI conversation
- Sentence generation exercises
- Advanced grammar evaluation
- Adaptive curriculum
- More detailed reading difficulty analysis

---

# 9. Design Principles

## Domain Separation

Language data and learner data should remain separate.

A sentence does not inherently have a difficulty.

Difficulty depends on:

- The learner
- Their vocabulary knowledge
- Their previous experience

---

## Event-Based Learning History

Learning outcomes should be represented as events:

Examples:

- VocabularyAttempt
- ReadingAttempt
- ConversationAttempt
- WritingAttempt

Progress should be calculated from these events.

---

## Extensibility

New learning activities should be possible without changing existing linguistic
models.
