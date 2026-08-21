"""
Domain model representing a single Chinese character.

A Character is an immutable Value Object that encapsulates a single Chinese
logogram. It forms the smallest linguistic unit recognised by the domain and
serves as the building block for higher-level concepts such as Tokens,
Sentences, and the User Vocabulary Profile.

Responsibilities:
    - Represent a single Chinese character.
    - Enforce domain invariants (e.g. exactly one valid character).
    - Provide value-based equality.

Non-responsibilities:
    - Pinyin resolution.
    - Stroke count lookup.
    - Radical lookup.
    - Database persistence.
    - NLP processing.

Design Notes:
    Character is modelled as a Value Object because it has no identity beyond
    its value. Two Character instances representing the same Chinese character
    are considered equal regardless of where they originate.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Character:
    symbol: str

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("Character symbol cannot be empty")

        if len(self.symbol) != 1:
            raise ValueError("Character must contain exactly one symbol")

        if not self._is_cjk(self.symbol):
            raise ValueError("Character must be a Chinese character")

    def __str__(self) -> str:
        return self.symbol

    @staticmethod
    def _is_cjk(value: str) -> bool:
        code = ord(value)
        return (
            0x4E00 <= code <= 0x9FFF  # CJK Unified Ideographs
            or 0x3400 <= code <= 0x4DBF  # CJK Extension A
            or 0x20000 <= code <= 0x2A6DF  # Extensions B+
        )
