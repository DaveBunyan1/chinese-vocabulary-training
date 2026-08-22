import re
from collections.abc import Sequence

import jieba

from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.text_analysis.sentence import Sentence
from chinese_learning.domain.text_analysis.token import Token
from chinese_learning.infrastructure.nlp.text_analysis_result import (
    TextAnalysisResult,
)

# Matches pure punctuation / symbols / whitespace
_PUNCTUATION_RE = re.compile(
    r"^[\s"
    r"\u3000-\u303F"  # CJK punctuation
    r"\uFF00-\uFFEF"  # Full-width punctuation
    r"\u2000-\u206F"  # General punctuation
    r"!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~"
    r"]+$"
)


def _is_punctuation(text: str) -> bool:
    return bool(_PUNCTUATION_RE.match(text))


def _extract_characters(tokens: Sequence[Token]) -> tuple[Character, ...]:
    """Return unique Characters in order of first appearance."""
    seen: set[str] = set()
    result: list[Character] = []

    for token in tokens:
        for char in token.text:
            if char not in seen:
                try:
                    result.append(Character(char))
                    seen.add(char)
                except ValueError:
                    # skip non-CJK characters (Latin, digits, etc.)
                    continue

    return tuple(result)


class AnalyseText:
    """
    Pure domain service: raw Chinese text → Sentence + unique Characters.

    - Punctuation is dropped from tokens but preserved in sentence.raw_text.
    - No persistence, no side effects.
    """

    def execute(self, raw_text: str) -> TextAnalysisResult:
        if not raw_text or not raw_text.strip():
            raise ValueError("raw_text cannot be empty")

        # jieba returns a generator of strings
        raw_tokens = jieba.cut(raw_text.strip())

        tokens = [Token(text=t) for t in raw_tokens if t and not _is_punctuation(t)]

        if not tokens:
            raise ValueError("No valid tokens found in text")

        sentence = Sentence(raw_text=raw_text.strip(), tokens=tokens)
        characters = _extract_characters(tokens)

        return TextAnalysisResult(sentence=sentence, characters=characters)
