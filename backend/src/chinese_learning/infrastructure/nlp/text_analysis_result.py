from dataclasses import dataclass

from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.text_analysis.sentence import Sentence


@dataclass(frozen=True, slots=True)
class TextAnalysisResult:
    sentence: Sentence
    characters: tuple[Character, ...]  # unique, order of first appearance
