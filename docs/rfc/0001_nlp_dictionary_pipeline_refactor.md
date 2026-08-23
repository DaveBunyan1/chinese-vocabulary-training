# RFC: Harden Text-Import NLP & Exposure Pipeline

**Status:** Draft  
**Author:** Dave Bunyan
**Branch / follow-up:** `refactor/nlp-dictionary-pipeline` (or similar)  
**Related:** Phase 4 vertical slice – “Build My Knowledge”

---

## 1. Context & Motivation

During the initial vertical slice release of the text import pipeline, the end-to-end integration (FastAPI + Jieba + CC-CEDICT + React/Vite) successfully demonstrated text analysis, vocabulary creation, HSK auto-tagging, and learner knowledge tracking.

However, several edge cases in token deduplication, dictionary lookup resolution, fallback handling, and HSK categorization were identified:

1. **Duplicate Token Crashes:** Sentences with repeated tokens (e.g., grammatical particles like `的`) trigger database `UniqueConstraint` violations when updating learner exposure metrics in a single transaction.
2. **Proper-Noun Surnames:** CEDICT lookups return obscure surname definitions (e.g., `坐 [Zuo4] /surname Zuo/`) due to unranked casing or entry priority logic.
3. **Missing Compound Terms:** Jieba tokenizes compound phrases (e.g., `坐在`, `村内`) that lack exact headwords in CC-CEDICT, leading to `[not found in CC-CEDICT]` responses.
4. **Composite HSK Words Unassigned:** HSK 3.0 lists root characters (`你`, `好` → HSK 1) but omits some common combined expressions like `你好`, leaving everyday vocabulary tagged as `null` / `Uncategorised`.
5. **Oversized CEDICT glosses:** Headwords like 就 produce definitions longer than VARCHAR(512), so inserts fail and the import returns 500.

This RFC proposes targeted refactors across the domain and infrastructure layers to make the NLP and exposure pipeline robust, accurate, and fully covered by integration tests.

---

## 2. Goals

- Make text import **idempotent and crash-free** for any realistic Chinese input (including repeated tokens).
- Improve **dictionary resolution quality** (prefer common senses over surname/obscure entries).
- Reduce **“not found”** noise for Jieba compounds that are not CEDICT headwords.
- Improve **HSK coverage** for high-frequency multi-character expressions where reasonable.
- Expand **integration tests** so these cases cannot regress.
- Keep changes **incremental**: fix the hard crash first, then validate behaviour on larger corpora before investing in deeper NLP changes.

## 3. Non-Goals

- Full multi-user auth / learner registration (still out of scope for this slice).
- Replacing Jieba or CEDICT with a different stack.
- Perfect HSK tagging of every possible compound or proper name.
- UI redesign beyond whatever is needed to surface clearer fallback states.
- Building a custom Chinese dictionary from scratch.

---

## 4. Proposed Design

### 4.0 Priority 0 — Persist full CEDICT meanings

- Change vocabulary_items.meaning from String(512) to Text.
- Migration to alter the column.
- Optional: truncate only in the API/UI for display, never at write time.

### 4.1 Priority 1 — Deduplicate before exposure updates (crash fix)

**Problem**  
`UpdateKnowledgeOnExposure` (and possibly import) receives a list that can contain the same `VocabularyId` / character more than once in one request. Bulk upsert/insert then violates a unique constraint on `(learner_id, vocabulary_id)` or `(learner_id, character)`.

**Proposal**

- Deduplicate **in the use case** (or at the router boundary) before loading existing knowledge or writing:
  - Characters: unique by character value
  - Vocabulary: unique by `VocabularyId`
- Prefer preserving order of first occurrence (stable dedupe) so behaviour is predictable in tests.
- Optionally count multiplicity and later feed it into `with_exposure` (e.g. increment `times_seen` by occurrence count in the same text). **v1 recommendation:** dedupe only (one exposure event per distinct item per import). Multiplicity can be a follow-up if product wants “seen 3 times in this paragraph”.

**Acceptance**

- Importing text with repeated particles (e.g. `的…的…的`) returns 200 and creates/updates each distinct knowledge row once.
- Integration test covers repeated tokens and repeated characters in one payload.

---

### 4.2 Priority 2 — CEDICT sense ranking (surname / obscure entries)

**Problem**  
Unranked multi-entry CEDICT lookups surface surname or rare senses first (e.g. `坐` → “surname Zuo”).

**Proposal (lightweight)**

- When multiple CEDICT entries match a headword, **score and pick the best**:
  - Prefer entries whose pinyin is **lowercase** (common convention: proper names often capitalised in CEDICT).
  - Penalise definitions matching patterns such as `/surname …/`, `/name of …/`, `/variant of …/` when a non-surname sense exists.
  - Prefer entries with more “general” gloss structure if needed (simple heuristic is enough for v1).
- Keep all alternate senses available later if we add a “other meanings” UI; for import, store **one primary** meaning + pinyin.

**Acceptance**

- `坐` (and similar) resolve to the common verb sense when present in CEDICT.
- Unit tests on a small fixture dictionary covering multi-entry headwords.

---

### 4.3 Priority 3 — Fallback for missing compound headwords

**Problem**  
Jieba emits tokens such as `坐在` / `村内` that are not CEDICT headwords → `[not found in CC-CEDICT]`.

**Proposal (staged)**

**Stage A (minimal, ship soon after P1)**

- If exact lookup fails:
  1. Try known **normalisations** (full-width, trivial variants) if not already done.
  2. Mark item as `meaning` = structured fallback (not a raw error string), e.g. `is_dictionary_miss=True` or meaning `"—"`, and still persist the token so knowledge tracking works.
  3. Optionally attempt **character-by-character** gloss join only for 2-char tokens as a _display_ hint (clearly labelled as approximate), without inventing a false headword.

**Stage B (if large-corpus analysis justifies it)**

- Secondary segmentation / longest CEDICT match inside the token.
- Optional user-editable definition on the knowledge view.

**Acceptance**

- Import never fails solely because a token is missing from CEDICT.
- UI/API can distinguish “real definition” vs “dictionary miss”.

---

### 4.4 Priority 4 — HSK tagging for common composites

**Problem**  
HSK lists include `你` and `好` but not always `你好`, so composites stay Uncategorised.

**Proposal (conservative)**

- Keep primary rule: **exact match** against exclusive HSK 3.0 lists.
- Add a **small curated override map** for ultra-high-frequency greetings/expressions that learners expect to see tagged (start tiny: `你好`, `谢谢`, `再见`, etc.), versioned in repo data—not inferred automatically from characters.
- Do **not** auto-assign “min(component levels)” globally; that mis-tags many compounds and invents non-syllabus items.

**Optional later research**

- If corpus analysis shows many near-misses, consider “derived from HSK components” as a _secondary_ label, separate from official HSK level.

**Acceptance**

- Override list is explicit, test-covered, and documented as non-official syllabus extensions.
- Default path remains exact HSK list lookup + Uncategorised.

---

## 5. Implementation plan

| Phase  | Work                                                                                                | Exit criteria                                       |
| ------ | --------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **A**  | Dedupe in exposure (and import path if needed) + regression tests                                   | No UniqueConstraint on repeated tokens; tests green |
| **A1** | meaning → Text + migration                                                                          | 就 (and similar) import without 500                 |
| **B**  | Run large real-world text samples through import; log dictionary misses, HSK nulls, odd definitions | Written findings note (counts + examples)           |
| **C**  | CEDICT ranking heuristics + tests                                                                   | Surname cases fixed for known fixtures              |
| **D**  | Dictionary-miss fallback contract (API + optional UI hint)                                          | No raw `[not found…]` as the only UX                |
| **E**  | Curated HSK composite overrides (small list)                                                        | Overrides applied + tests                           |
| **F**  | Only if B justifies it: deeper compound resolution                                                  | Separate mini-RFC or ticket                         |

**Recommended order:** A → B → then C/D/E based on data from B.

---

## 6. Testing strategy

- **Unit:** CEDICT ranker; HSK lookup + overrides; pure dedupe helper.
- **Integration:**
  - Text with repeated `的` / repeated words
  - Mix of known HSK words, surname-prone chars, Jieba compounds missing from CEDICT
  - Second import still idempotent on vocabulary creation
- **Corpus smoke (manual/scripted):** 1–5k characters of varied text (news, dialogue, HSK practice); export CSV of `{token, meaning, hsk_level, is_miss}` for review.

---

## 7. Risks & open questions

| Risk / question                                                                 | Mitigation                                                         |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Counting one exposure per distinct token under-counts repetition in a paragraph | Document v1 behaviour; optional multiplicity later                 |
| Surname heuristic may demote a legitimate proper-name reading                   | Prefer non-surname only when both exist; allow future sense picker |
| Character-join fallback may look like a false dictionary entry                  | Label clearly as approximate / miss                                |
| HSK overrides drift from official syllabus                                      | Keep list small, named, and documented                             |
| Jieba segmentation quality drives many “misses”                                 | Measure in Phase B before heavy investment                         |

**Open questions**

1. Should one import increment `times_seen` by occurrence count or always +1 per distinct item?
2. Should dictionary misses be stored as vocabulary rows at all, or skipped until the user confirms?
3. Do we expose `is_dictionary_miss` / `hsk_source` (`official` | `override` | `none`) on the API for the frontend?

---

## 8. Success metrics

- Zero 500s on import from unique-constraint / duplicate exposure paths.
- ≥ N high-frequency sample sentences import cleanly (define N after Phase B).
- Material drop in “surname-only” primary definitions on a fixed evaluation set.
- Dictionary-miss rate measured and either accepted or reduced via Stage B work.
- All new behaviours covered by automated tests in CI.

---

## 9. Appendix — Example failure cases

| Input snippet   | Observed issue                        | Target behaviour                                                |
| --------------- | ------------------------------------- | --------------------------------------------------------------- |
| `…的…的…`       | UniqueConstraint on knowledge write   | Single knowledge row, 200 OK                                    |
| `坐在椅子上`    | `坐` → surname sense                  | Common verb sense preferred                                     |
| `坐在` as token | `[not found in CC-CEDICT]`            | Persist token; structured miss / better fallback                |
| `你好`          | `hsk_level: null`                     | Override → HSK 1 (if on curated list) or explicit Uncategorised |
| `就`            | 500 / value too long for varchar(512) | Store full gloss; 200 OK                                        |

---
