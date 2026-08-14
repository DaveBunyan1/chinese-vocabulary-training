from dataclasses import dataclass

from chinese_learning.domain.learner.word_status import WordStatus
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyItem


@dataclass(frozen=True)
class VocabularyKnowledge:
    vocabulary: VocabularyItem
    status: WordStatus
