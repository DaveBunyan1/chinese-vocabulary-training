```text
Learner
   │
   ▼
UserVocabularyProfile
   │
   ├────────► SentenceAnalysisService
   │                 │
   │                 ▼
   │           Sentence
   │                 │
   ▼                 ▼
ReviewQueueService  PromptContextBuilder
   │                 │
   ▼                 ▼
PracticeSession   ChatSession
   │                 │
   └────────► RecallAttempt
                     │
                     ▼
           ProgressAnalysisService
```
