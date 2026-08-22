from dataclasses import dataclass

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyItem
from chinese_learning.infrastructure.nlp.analyse_text import AnalyseText
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.nlp.text_analysis_result import (
    TextAnalysisResult,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)


@dataclass(frozen=True, slots=True)
class ImportVocabularyResult:
    vocabulary_items: tuple[VocabularyItem, ...]
    created_count: int
    existing_count: int
    analysis: TextAnalysisResult


class ImportVocabularyFromText:
    def __init__(
        self,
        analyse_text: AnalyseText,
        dictionary: CedictDictionary,
        vocabulary_repo: VocabularyItemRepository,
    ) -> None:
        self._analyse_text = analyse_text
        self._dictionary = dictionary
        self._vocabulary_repo = vocabulary_repo

    async def execute(
        self, learner_id: LearnerId, raw_text: str
    ) -> ImportVocabularyResult:
        # 1. Analyse the text
        analysis = self._analyse_text.execute(raw_text)

        # 2. Resolve each token to a VocabularyItem
        items: list[VocabularyItem] = []
        created = 0
        existing = 0

        for token in analysis.sentence.tokens:
            # Prefer an already-persisted item with the same text
            existing_item = await self._vocabulary_repo.get_by_text(token.text)

            if existing_item is not None:
                items.append(existing_item)
                existing += 1
            else:
                # Look up (or generate) pinyin + meaning and persist
                new_item = self._dictionary.lookup(token.text)
                await self._vocabulary_repo.save(new_item)
                items.append(new_item)
                created += 1

        return ImportVocabularyResult(
            vocabulary_items=tuple(items),
            created_count=created,
            existing_count=existing,
            analysis=analysis,
        )
