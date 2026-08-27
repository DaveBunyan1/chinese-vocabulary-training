# App Development Roadmap & TODO

## Bug Fixes

- [x] **HSK Level Filtering:** Fix `ListVocabularyDashboard` so filtering by HSK level correctly updates and narrows the returned item count.
- [x] **Dashboard Unit Tests:** Fix broken `test_filters_by_status` assertion failure in `test_list_vocabulary_dashboard.py` caused by repository mock mismatches.
- [ ] **Definition Sanitization:** Run a cleaning script over vocabulary dictionary definitions to strip out parenthetical glosses, usage notes, and bound-form entries (e.g. reduce `他` from full dictionary note down to `he; him; his`).
- [ ] **Flexible Definition Matching:** Update practice answer validation to parse multi-meaning target strings into single accepted terms so answers like `"I"` pass for `"I; me; my"`.

---

## Features & Enhancements

### Category & Knowledge Management

- [ ] **Category CRUD:** Add support for editing and deleting custom user categories.
- [ ] **Vocab-to-Character Linking:** Link vocabulary knowledge entities to individual constituent character knowledge records.
- [ ] **Expanded Knowledge Statuses:** Introduce `KnowledgeStatus.UNKNOWN` (or equivalent) for sentence-based character recognition tests without automatically promoting words to `NEW`.

### Input & Pedagogical Feedback

- [ ] **Pinyin Tone Number Parsing:** Allow numbered Pinyin input (e.g., `ni3`) during practice while automatically rendering tone diacritics in UI output (`nǐ`).
- [ ] **Rich Error Feedback:** Overhaul practice session feedback on incorrect answers to provide detailed explanations and diagnostic hints.

---

## Frontend & UI/UX

- [ ] **Home Dashboard:** Create a primary landing page showing a aggregate learner profile metrics, recent activity, and a global language switcher.
- [ ] **Dark Mode & Mobile Layout:** Implement a global dark theme and refine responsive styling across mobile screen breakpoints.
- [ ] **Content Copy Audit:** Review and polish all microcopy, label descriptions, and UI instructions for consistency.

---

## Testing & Refactoring

- [ ] **Dashboard Persistence Tests:** Write comprehensive integration/unit tests for dashboard query methods across persistence repositories.

---

### Documentation

- [ ] **README.md**: Update README.md to align with MVP (after finishing phase 7) and add screenshots etc. where applicable
