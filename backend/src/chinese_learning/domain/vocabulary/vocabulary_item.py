from dataclasses import dataclass


@dataclass(frozen=True)
class VocabularyId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class VocabularyItem:
    """
    A single lexical sense of a Chinese word/phrase.

    HSK syllabi list sense-level entries: the same surface form can appear
    more than once with different POS / pinyin / meaning (e.g. 过 verb vs
    particle, 花 "spend" vs "flower"). Identity is therefore (text, pos),
    not text alone.
    """

    id: VocabularyId
    text: str
    pinyin: str
    meaning: str
    pos: str | None = None  # e.g. "verb", "noun", "auxiliary"; None/"" = unspecified

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Vocabulary text cannot be empty")

        if not self.pinyin.strip():
            raise ValueError("Vocabulary pinyin cannot be empty")

        if not self.meaning.strip():
            raise ValueError("Vocabulary meaning cannot be empty")

    @property
    def pos_key(self) -> str:
        """Normalised POS used for uniqueness and lookups."""
        return (self.pos or "").strip().lower()
