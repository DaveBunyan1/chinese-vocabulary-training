# application/use_cases/update_knowledge_on_exposure.py

from dataclasses import dataclass
from datetime import UTC, datetime

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId
from chinese_learning.infrastructure.persistence.repositories.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)


@dataclass(frozen=True, slots=True)
class UpdateKnowledgeOnExposureResult:
    character_knowledge_updated: int
    vocabulary_knowledge_updated: int


class UpdateKnowledgeOnExposure:
    """
    Records passive exposure for a set of characters and vocabulary items.

    - Creates a NEW knowledge record if none exists.
    - Calls with_exposure() on existing records.
    - Persists everything in bulk.
    """

    def __init__(
        self,
        character_knowledge_repo: CharacterKnowledgeRepository,
        vocabulary_knowledge_repo: VocabularyKnowledgeRepository,
    ) -> None:
        self._character_repo = character_knowledge_repo
        self._vocabulary_repo = vocabulary_knowledge_repo

    async def execute(
        self,
        learner_id: LearnerId,
        characters: list[Character],
        vocabulary_ids: list[VocabularyId],
        *,
        at: datetime | None = None,
    ) -> UpdateKnowledgeOnExposureResult:
        now = at or datetime.now(UTC)

        char_updated = await self._update_characters(learner_id, characters, now)
        vocab_updated = await self._update_vocabulary(learner_id, vocabulary_ids, now)

        return UpdateKnowledgeOnExposureResult(
            character_knowledge_updated=char_updated,
            vocabulary_knowledge_updated=vocab_updated,
        )

    async def _update_characters(
        self,
        learner_id: LearnerId,
        characters: list[Character],
        at: datetime,
    ) -> int:
        if not characters:
            return 0

        # Load existing records in one query
        existing = {
            str(k.character): k
            for k in await self._character_repo.get_many(learner_id, characters)
        }

        to_save: list[CharacterKnowledge] = []

        for char in characters:
            key = str(char)
            if key in existing:
                updated = existing[key].with_exposure(at)
            else:
                updated = CharacterKnowledge(
                    learner_id=learner_id,
                    character=char,
                    status=KnowledgeStatus.NEW,
                    times_seen=1,
                    first_seen_at=at,
                    last_seen_at=at,
                )
            to_save.append(updated)

        await self._character_repo.save_many(to_save)
        return len(to_save)

    async def _update_vocabulary(
        self,
        learner_id: LearnerId,
        vocabulary_ids: list[VocabularyId],
        at: datetime,
    ) -> int:
        if not vocabulary_ids:
            return 0

        existing = {
            str(k.vocabulary_id): k
            for k in await self._vocabulary_repo.get_many(learner_id, vocabulary_ids)
        }

        to_save: list[VocabularyKnowledge] = []

        for vid in vocabulary_ids:
            key = str(vid)
            if key in existing:
                updated = existing[key].with_exposure(at)
            else:
                updated = VocabularyKnowledge(
                    learner_id=learner_id,
                    vocabulary_id=vid,
                    status=KnowledgeStatus.NEW,
                    times_seen=1,
                    first_seen_at=at,
                    last_seen_at=at,
                )
            to_save.append(updated)

        await self._vocabulary_repo.save_many(to_save)
        return len(to_save)
