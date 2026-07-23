from collections.abc import Sequence
from dataclasses import dataclass

from chinese_learning.domain.text_analysis.token import Token


@dataclass(frozen=True)
class Sentence:
    _tokens: tuple[Token, ...]

    def __init__(self, tokens: Sequence[Token]) -> None:
        if not tokens:
            raise ValueError("Sentence must contain at least one token")

        object.__setattr__(
            self,
            "_tokens",
            tuple(tokens),
        )

    @property
    def tokens(self) -> tuple[Token, ...]:
        return self._tokens
