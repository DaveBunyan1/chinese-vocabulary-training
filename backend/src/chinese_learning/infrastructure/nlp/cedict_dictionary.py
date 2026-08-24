from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from pypinyin import Style, lazy_pinyin

from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)

_LINE_RE = re.compile(
    r"^(?P<traditional>\S+)\s+(?P<simplified>\S+)\s+\[(?P<pinyin>[^\]]+)\]\s+/(?P<meaning>.+)/$"
)

_SURNAME_RE = re.compile(r"(?i)\bsurname\b")
_PROPER_RE = re.compile(
    r"(?i)\b(surname|name of|place name|county|district|river|mountain)\b"
)

NOT_FOUND_MEANING = "—"


class CedictDictionary:
    """
    In-memory CC-CEDICT lookup.

    - Prefers simplified form.
    - When multiple entries exist, ranks senses (common > surname/proper).
    - Falls back to pypinyin when the word is missing from the dictionary.
    """

    def __init__(self, cedict_path: Path | str) -> None:
        self._entries: dict[str, list[tuple[str, str]]] = {}
        self._load(Path(cedict_path))

    def _load(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"CC-CEDICT file not found: {path}")

        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                match = _LINE_RE.match(line)
                if not match:
                    continue

                simplified = match.group("simplified")
                pinyin = match.group("pinyin")
                meaning = match.group("meaning").replace("/", "; ").strip("; ")

                self._entries.setdefault(simplified, []).append((pinyin, meaning))

    def lookup(self, text: str) -> VocabularyItem:
        text = text.strip()
        if not text:
            raise ValueError("Cannot look up empty text")

        if text in self._entries:
            pinyin, meaning = self._select_best(self._entries[text])
        else:
            # Fallback for words not in CEDICT
            pinyin = " ".join(lazy_pinyin(text, style=Style.TONE3))
            meaning = NOT_FOUND_MEANING

        return VocabularyItem(
            id=VocabularyId(str(uuid4())),
            text=text,
            pinyin=pinyin,
            meaning=meaning,
        )

    @staticmethod
    def _select_best(senses: list[tuple[str, str]]) -> tuple[str, str]:
        """
        Rank senses for learner-facing primary gloss.

        Higher score wins. File order is a weak tie-breaker only.
        """
        if len(senses) == 1:
            return senses[0]

        def score(item: tuple[str, str]) -> tuple[int]:
            pinyin, meaning = item
            s = 0

            # Prefer ordinary vocabulary over surname / geo proper names
            if _SURNAME_RE.search(meaning):
                s -= 100
            elif _PROPER_RE.search(meaning):
                s -= 50

            # CEDICT often capitalises proper-name pinyin (e.g. Zhong4 vs zhong1)
            if pinyin[:1].isupper():
                s -= 20

            # Prefer slightly richer non-surname glosses over a single short label
            if not _SURNAME_RE.search(meaning):
                s += min(len(meaning), 80) // 20

            return (s,)

        # Max by score; stable with respect to original order on ties via enumerate
        best = max(
            enumerate(senses),
            key=lambda pair: (score(pair[1]), -pair[0]),
        )
        return best[1]

    def known_words(self) -> set[str]:
        return set(self._entries.keys())

    def contains(self, text: str) -> bool:
        return text.strip() in self._entries
