"""
Ensure character knowledge records exist for every constituent character
of the given vocabulary items (vocab → character linking).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.text_analysis.character import (
    Character,
    characters_from_text,
)
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyItem
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)


@dataclass(frozen=True, slots=True)
class LinkVocabularyCharactersResult:
    characters_touched: int
    characters_created: int
    characters_updated: int


class LinkVocabularyCharacters:
    """
    For each vocabulary item text, extract CJK characters and ensure the
    learner has CharacterKnowledge for each (create NEW or record exposure).
    """

    def __init__(self, character_knowledge_repo: CharacterKnowledgeRepository) -> None:
        self._character_repo = character_knowledge_repo

    async def execute(
        self,
        learner_id: LearnerId,
        items: list[VocabularyItem] | tuple[VocabularyItem, ...],
        *,
        at: datetime | None = None,
    ) -> LinkVocabularyCharactersResult:
        now = at or datetime.now(UTC)

        chars: list[Character] = []
        seen: set[str] = set()
        for item in items:
            for ch in characters_from_text(item.text):
                key = str(ch)
                if key not in seen:
                    seen.add(key)
                    chars.append(ch)

        if not chars:
            return LinkVocabularyCharactersResult(0, 0, 0)

        existing = {
            str(k.character): k
            for k in await self._character_repo.get_many(learner_id, chars)
        }

        to_save: list[CharacterKnowledge] = []
        created = 0
        updated = 0

        for char in chars:
            key = str(char)
            if key in existing:
                to_save.append(existing[key].with_exposure(now))
                updated += 1
            else:
                to_save.append(
                    CharacterKnowledge(
                        learner_id=learner_id,
                        character=char,
                        status=KnowledgeStatus.NEW,
                        times_seen=1,
                        first_seen_at=now,
                        last_seen_at=now,
                    )
                )
                created += 1

        await self._character_repo.save_many(to_save)
        return LinkVocabularyCharactersResult(
            characters_touched=len(to_save),
            characters_created=created,
            characters_updated=updated,
        )
