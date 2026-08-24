# ADR: NLP dictionary & import pipeline choices

**Status:** Accepted  
**Date:** 2026-08-24  
**Branch:** `refactor/nlp-dictionary-pipeline`  
**Context:** RFC – Harden Text-Import NLP & Exposure Pipeline

---

### Context

We need reliable vocabulary import from arbitrary Chinese text using Jieba + CC-CEDICT + HSK 3.0 lists, without crashing or flooding the learner profile with noise, while keeping the implementation simple enough for a single-learner vertical slice.

---

### Decision 1 — Dedupe in the exposure use case (and unique items on import)

**Decision:** Deduplicate vocabulary IDs and characters in `UpdateKnowledgeOnExposure` before load/save. Import builds a unique-by-text (piece) list.

**Why:** Jieba emits repeated tokens; the domain identity is the lemma/surface, not each occurrence. Fixing this in the use case protects all callers, not only the HTTP route.

**Alternative rejected:** Count every repetition toward `times_seen` in one request — deferred; v1 is one passive exposure event per distinct item per import.

---

### Decision 2 — `meaning` as `Text`

**Decision:** Store full CEDICT glosses in an unbounded text column.

**Why:** Headwords like `就` exceed 512 characters; truncation at the DB layer caused hard failures.

**Alternative rejected:** Truncate on write — loses data and breaks sense ranking edge cases. Prefer truncate only in UI if needed.

---

### Decision 3 — Rank CEDICT senses instead of “first line wins”

**Decision:** Index all senses per simplified form; select primary sense with a heuristic (penalise `surname` / strong proper-name patterns and capitalised pinyin).

**Why:** CC-CEDICT often lists surname lines first; first-line caching systematically degraded high-frequency characters.

**Alternative rejected:** Manual sense picker in UI (later product feature). Heuristic is enough for import quality.

---

### Decision 4 — Soft miss + studyable-token filter

**Decision:** Missing headwords get pypinyin + meaning `—`. Import skips pure Latin, pure digits, and non-Han punctuation.

**Why:** Error-shaped strings are poor UX; English/digits from mixed corpora are not Chinese study targets.

**Alternative rejected:** Dropping all misses entirely — still useful to allow single rare Han characters through soft miss when segmentation cannot do better.

---

### Decision 5 — Sub-segment only on exact CEDICT miss

**Decision:** If the Jieba token is in CEDICT, keep it. Otherwise forward maximum-match against CEDICT keys and import pieces.

**Why:** Corpus showed ~22% exact misses, largely multi-character spans whose parts exist in CEDICT. Max-match is simple, deterministic, and needs no extra models.

**Alternatives rejected:**

| Option                                    | Reason                            |
| ----------------------------------------- | --------------------------------- |
| Always character-split                    | Destroys real multi-char words    |
| Min HSK level of components for compounds | Invents non-syllabus “HSK” labels |
| Second segmenter / ML NER                 | Out of scope for this branch      |

**Trade-off:** Personal names may split into ordinary words. Accepted for v1.

---

### Decision 6 — HSK remains exact-list only

**Decision:** No bulk overrides; Uncategorised when not on the HSK 3.0 map.

**Why:** After segmentation, ~35%+ of real glossed pieces are legitimately off-list in mixed text. Overrides would be arbitrary without a tight product list.

---

### Consequences

**Positive**

- Stable import under repetition and long glosses.
- Better default definitions for common characters.
- Near-full CEDICT coverage on post-split pieces in the sample corpus.
- Cleaner learner vocabulary (less Latin/digit noise).

**Negative / residual**

- Name and novel-specific terms are imperfect.
- Very long glosses still verbose in API/UI.
- Historical rows may still hold pre-ranker meanings until re-import/re-enrich.

**Follow-up ADRs (when needed):** auth-scoped learner; user-editable definitions; optional occurrence-weighted exposure.
