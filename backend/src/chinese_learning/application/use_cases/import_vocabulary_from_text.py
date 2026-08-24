from dataclasses import dataclass

from chinese_learning.application.use_cases.assign_hsk_category import AssignHSKCategory
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyItem
from chinese_learning.infrastructure.nlp.analyse_text import AnalyseText
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.nlp.text_analysis_result import (
    TextAnalysisResult,
)
from chinese_learning.infrastructure.nlp.token_filters import is_studyable_chinese_token
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
        assign_hsk: AssignHSKCategory,
    ) -> None:
        self._analyse_text = analyse_text
        self._dictionary = dictionary
        self._vocabulary_repo = vocabulary_repo
        self._assign_hsk = assign_hsk

    async def execute(
        self, learner_id: LearnerId, raw_text: str
    ) -> ImportVocabularyResult:
        analysis = self._analyse_text.execute(raw_text)

        items_by_text: dict[str, VocabularyItem] = {}
        created = 0
        existing = 0
        newly_created: list[VocabularyItem] = []
        skipped = 0

        for token in analysis.sentence.tokens:
            if not is_studyable_chinese_token(token.text):
                skipped += 1
                continue
            if token.text in items_by_text:
                # Already handled this surface form in this import
                continue

            existing_item = await self._vocabulary_repo.get_by_text(token.text)

            if existing_item is not None:
                items_by_text[token.text] = existing_item
                existing += 1
            else:
                new_item = self._dictionary.lookup(token.text)
                await self._vocabulary_repo.save(new_item)
                items_by_text[token.text] = new_item
                newly_created.append(new_item)
                created += 1

        items = list(items_by_text.values())

        if newly_created:
            await self._assign_hsk.execute(newly_created)

        return ImportVocabularyResult(
            vocabulary_items=tuple(items),
            created_count=created,
            existing_count=existing,
            analysis=analysis,
        )
