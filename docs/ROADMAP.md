```text
Phase 1: Foundation & Tooling
├── chore/project-skeleton
├── chore/add-development-tooling
└── chore/infrastructure-boilerplate


Phase 2: Core Domain
├── feat/domain-character-model
├── feat/domain-token-model
├── feat/domain-sentence-aggregate
├── feat/domain-vocabulary-item
└── feat/domain-learner-knowledge


Phase 3: Persistence & Infrastructure
├── feat/database-setup                        (SQLAlchemy / async, Alembic)
├── feat/repositories-learner-knowledge        (VocabularyKnowledge + CharacterKnowledge)
├── feat/repositories-linguistic               (Sentence, VocabularyItem, Category)
├── feat/repositories-identity                 (User + LearnerProfile)
└── feat/seed-basic-categories                 (HSK levels + a few topic categories)


Phase 4: First Vertical Slice – “Build My Knowledge”
Goal: A learner can paste Chinese text and the system builds their vocabulary + character knowledge profile, organised by categories.

├── feat/analyse-text-usecase                  (jieba or similar → Tokens + Characters)
├── feat/import-vocabulary-from-text
├── feat/update-knowledge-on-exposure          (with_exposure calls)
├── feat/assign-categories-to-vocabulary
├── feat/rest-api-text-import
└── feat/frontend-text-import-and-knowledge-view


Phase 5: Vocabulary & Character Practice (Core MVP)
Goal: Practise recall and recognition filtered by category / subcategory / knowledge status.

├── feat/domain-exercise-and-question
├── feat/domain-answer-attempt
├── feat/generate-vocabulary-recall-exercise   (by category + status)
├── feat/generate-character-recognition-exercise
├── feat/score-and-update-knowledge            (with_success / with_failure)
├── feat/rest-api-practice
└── feat/frontend-practice-session             (simple, clean UI)


Phase 6: Knowledge Dashboard & Filtering
├── feat/vocabulary-dashboard                  (filter by category, status, HSK…)
├── feat/character-dashboard
├── feat/category-management-ui                (create subcategories, assign items)
└── feat/basic-progress-stats                  (derived from the knowledge records)


Phase 7: Polish & Real Learning Loop
├── feat/spaced-repetition-fields              (start using next_review_at etc.)
├── feat/review-queue-service
├── feat/weighted-item-selection
└── feat/frontend-smart-review


Phase 8+: Future (AI conversation, sentence construction, deep reading analysis, etc.)
```
