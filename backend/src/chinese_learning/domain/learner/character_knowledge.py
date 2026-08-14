from dataclasses import dataclass

from chinese_learning.domain.learner.word_status import WordStatus
from chinese_learning.domain.text_analysis.character import Character


@dataclass(frozen=True)
class CharacterKnowledge:
    character: Character
    status: WordStatus
