## RFC: Harden Text-Import NLP & Exposure Pipeline

**Status:** Implemented (branch `refactor/nlp-dictionary-pipeline`)  
**Related:** Phase 4 – “Build My Knowledge”

---

### 1. Context & motivation

The vertical slice (analyse → vocabulary → HSK tags → knowledge exposure → UI) worked end-to-end, but real text exposed several pipeline gaps:

1. **Duplicate token crashes** — Repeated surfaces (e.g. `的`) produced duplicate `VocabularyId`s in one exposure batch and violated unique constraints.
2. **Oversized CEDICT glosses** — Entries like `就` exceeded `VARCHAR(512)` and caused insert failures.
3. **Surname-first definitions** — Loading “first CEDICT line wins” preferred proper-name senses (`教` → surname Jiao).
4. **Hard dictionary misses** — Missing headwords surfaced as `[not found in CC-CEDICT]`.
5. **Non-lexical noise** — Latin, digits, and punctuation were treated as study vocabulary.
6. **Jieba compounds without headwords** — Spans like `坐在` / `课堂练习` missed CEDICT as wholes (~22% of unique studyable tokens in corpus).

---

### 2. Goals (achieved)

- Crash-free import for repetitive Chinese text.
- Persist full dictionary glosses.
- Prefer learner-useful CEDICT senses over surname-first lines.
- Soft misses; filter non-Chinese junk on import.
- Sub-segment exact misses against the CEDICT lexicon so pieces resolve to real glosses.
- Measure impact on a mixed corpus (novels, news, HSK-adjacent, mixed).

### 3. Non-goals (unchanged)

- Auth / multi-learner registration.
- Replacing Jieba or CEDICT.
- Perfect HSK coverage or bulk “component min-level” HSK assignment.
- Full NER for literary names.

---

### 4. Design (as built)

| Area                 | Decision                                                                                                                                   |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Exposure**         | Dedupe characters and vocabulary IDs inside `UpdateKnowledgeOnExposure` (first occurrence wins; +1 `times_seen` per call, not per repeat). |
| **Import list**      | `ImportVocabularyFromText` keeps unique surface forms (and unique pieces after split).                                                     |
| **Schema**           | `vocabulary_items.meaning`: `String(512)` → `Text`.                                                                                        |
| **CEDICT load**      | Collect **all** senses per simplified headword; `_select_best` ranks (penalise surname/proper, capitalised pinyin).                        |
| **Miss**             | Fallback pinyin via pypinyin; meaning `—` (not an error string).                                                                           |
| **Token filter**     | `is_studyable_chinese_token`: require Han; reject pure digits, pure Latin, punct-only.                                                     |
| **Sub-segmentation** | If token ∉ CEDICT → forward **max-match** on CEDICT keys → lookup each piece. If token ∈ CEDICT → do not split.                            |
| **HSK**              | Exact list lookup only; Uncategorised otherwise. No bulk composite overrides.                                                              |

---

### 5. Corpus validation (post-implementation)

Same sample set (2 novel excerpts, 2 news stories, mixed, HSK course blurb):

| Metric                      | Approximate result              |
| --------------------------- | ------------------------------- |
| Jieba studyable tokens      | ~14 025                         |
| Sub-segmentation expansions | ~1 799                          |
| Unique pieces after split   | ~3 413                          |
| Dictionary misses (pieces)  | **~0%**                         |
| HSK null (non-miss pieces)  | ~36%                            |
| Odd meanings                | ~15 (down from ~70 pre-ranking) |

Earlier **~22%** miss rate was largely “compound not a CEDICT headword,” not unrecoverable text.

---

### 6. Implementation map

| Phase | Work                         | Status                              |
| ----- | ---------------------------- | ----------------------------------- |
| A     | Dedupe import + exposure     | Done                                |
| A1    | `meaning` → `Text`           | Done                                |
| B     | Corpus script + findings     | Done                                |
| C     | CEDICT multi-sense ranking   | Done                                |
| D     | Soft miss + studyable filter | Done                                |
| D+    | Max-match sub-segmentation   | Done                                |
| E     | Curated HSK overrides        | **Deferred** (data did not justify) |

---

### 7. Risks & follow-ups

| Topic            | Notes                                                                                                             |
| ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| Names (`铁柱`)   | May split into ordinary words; acceptable for v1 study lists.                                                     |
| Multiplicity     | One exposure per distinct item per import; not per occurrence count.                                              |
| Existing DB rows | Old surname-first / long truncated meanings need re-enrich if desired.                                            |
| Future           | Optional `is_dictionary_miss` on API; UI truncation of long glosses; tiny HSK override list only if product asks. |

---

### 8. Success criteria

- [x] No unique-constraint 500s on repeated particles
- [x] `就` and similar import successfully
- [x] Fewer surname-primary glosses (odd-sense count ↓)
- [x] No `[not found in CC-CEDICT]` as stored meaning
- [x] Latin/digits not imported as vocabulary
- [x] Compound misses largely resolved via sub-segmentation (piece miss ~0% on corpus)
