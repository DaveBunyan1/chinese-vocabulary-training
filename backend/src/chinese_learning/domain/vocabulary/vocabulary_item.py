from dataclasses import dataclass


@dataclass(frozen=True)
class VocabularyId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class VocabularyItem:
    id: VocabularyId
    text: str
    pinyin: str
    meaning: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Vocabulary text cannot be empty")

        if not self.pinyin.strip():
            raise ValueError("Vocabulary pinyin cannot be empty")

        if not self.meaning.strip():
            raise ValueError("Vocabulary meaning cannot be empty")
