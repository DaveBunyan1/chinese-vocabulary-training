"""
Domain model representing a Chinese text token.

A Token is an immutable Value Object representing a meaningful semantic unit
within Chinese text.

Token identity is based solely on its textual representation. Linguistic
metadata such as pinyin, part of speech, and vocabulary information are derived
by external services and are intentionally excluded from this domain model.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Token text cannot be empty")
