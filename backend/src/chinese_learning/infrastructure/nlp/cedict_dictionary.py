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


class CedictDictionary:
    """
    In-memory CC-CEDICT lookup.

    - Prefers simplified form.
    - Falls back to pypinyin when the word is missing from the dictionary.
    """

    def __init__(self, cedict_path: Path | str) -> None:
        self._entries: dict[str, tuple[str, str]] = {}  # text → (pinyin, meaning)
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

                # Keep the first entry we see for a given simplified form
                if simplified not in self._entries:
                    self._entries[simplified] = (pinyin, meaning)

    def lookup(self, text: str) -> VocabularyItem:
        text = text.strip()
        if not text:
            raise ValueError("Cannot look up empty text")

        if text in self._entries:
            pinyin, meaning = self._entries[text]
        else:
            # Fallback for words not in CEDICT
            pinyin = " ".join(lazy_pinyin(text, style=Style.TONE3))
            meaning = "[not found in CC-CEDICT]"

        return VocabularyItem(
            id=VocabularyId(str(uuid4())),
            text=text,
            pinyin=pinyin,
            meaning=meaning,
        )
