Changes:
A: Updated ImportVocabularyFromText to only give unique output
A1: Changed meaning to be Text instead of string(512)

## Phase B conclusion (corpus ~3.8k unique tokens)

- Pipeline is stable on real novel/news/HSK-adjacent text after P0/P1.
- ~22% non-junk tokens miss CEDICT exact match; many are English, names, or Jieba multi-char spans.
- ~28% of glossed tokens are outside HSK lists — expected; exact-list policy remains correct.
- Surname- and abbreviation-first CEDICT senses are a recurring quality issue on high-frequency characters.
- Next: (C) rank CEDICT senses; filter Latin/digits; (D) structured misses; HSK overrides only as a small explicit list.
