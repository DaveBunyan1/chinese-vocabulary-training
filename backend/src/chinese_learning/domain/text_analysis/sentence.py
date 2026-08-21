from collections.abc import Sequence
from dataclasses import dataclass

from chinese_learning.domain.text_analysis.token import Token


@dataclass(frozen=True)
class Sentence:
    _tokens: tuple[Token, ...]
    raw_text: str

    def __init__(self, raw_text: str, tokens: Sequence[Token]) -> None:
        if not raw_text.strip():
            raise ValueError("Sentence raw_text cannot be empty")
        if not tokens:
            raise ValueError("Sentence must contain at least one token")

        object.__setattr__(self, "raw_text", raw_text)
        object.__setattr__(
            self,
            "_tokens",
            tuple(tokens),
        )

    def __str__(self):
        return self.raw_text

    @property
    def tokens(self) -> tuple[Token, ...]:
        return self._tokens
