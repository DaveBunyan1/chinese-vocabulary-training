"""
List characters for a learner with optional knowledge-status and search filters.
"""

from __future__ import annotations

from dataclasses import dataclass

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)


@dataclass(frozen=True, slots=True)
class CharacterDashboardRow:
    character: str
    pinyin: str
    meaning: str
    status: str
    successful_recognitions: int
    failed_recognitions: int
    correct_pinyin_count: int
    times_seen: int
    last_practised_at: str | None
    last_seen_at: str | None


@dataclass(frozen=True, slots=True)
class ListCharacterDashboardResult:
    items: tuple[CharacterDashboardRow, ...]
    total: int
    status_counts: dict[str, int]


class ListCharacterDashboard:
    """
    Build a filtered character dashboard for one learner.

    Enriches each character with pinyin/meaning via CEDICT.
    """

    def __init__(
        self,
        character_knowledge_repo: CharacterKnowledgeRepository,
        dictionary: CedictDictionary,
    ) -> None:
        self._knowledge_repo = character_knowledge_repo
        self._dictionary = dictionary

    async def execute(
        self,
        learner_id: LearnerId,
        *,
        knowledge_status: KnowledgeStatus | None = None,
        search: str | None = None,
    ) -> ListCharacterDashboardResult:
        raw_counts = await self._knowledge_repo.count_by_status(learner_id)
        status_counts = {s.value: int(c) for s, c in raw_counts.items()}
        for key in ("new", "learning", "known"):
            status_counts.setdefault(key, 0)

        # Load all, filter in memory (avoids SQLEnum string-comparison issues)
        knowledge_list = await self._knowledge_repo.get_all_for_learner(learner_id)
        if knowledge_status is not None:
            knowledge_list = [k for k in knowledge_list if k.status is knowledge_status]

        needle = search.strip().casefold() if search else None

        rows: list[CharacterDashboardRow] = []
        for knowledge in knowledge_list:
            row = self._to_row(knowledge)
            if needle and not self._matches_search(row, needle):
                continue
            rows.append(row)

        rows.sort(key=lambda r: r.character)

        return ListCharacterDashboardResult(
            items=tuple(rows),
            total=len(rows),
            status_counts=status_counts,
        )

    def _to_row(self, knowledge: CharacterKnowledge) -> CharacterDashboardRow:
        symbol = str(knowledge.character)
        entry = self._dictionary.lookup(symbol)
        return CharacterDashboardRow(
            character=symbol,
            pinyin=entry.pinyin,
            meaning=entry.meaning,
            status=knowledge.status.value,
            successful_recognitions=knowledge.successful_recognitions,
            failed_recognitions=knowledge.failed_recognitions,
            correct_pinyin_count=knowledge.correct_pinyin_count,
            times_seen=knowledge.times_seen,
            last_practised_at=(
                knowledge.last_practised_at.isoformat()
                if knowledge.last_practised_at
                else None
            ),
            last_seen_at=(
                knowledge.last_seen_at.isoformat() if knowledge.last_seen_at else None
            ),
        )

    @staticmethod
    def _matches_search(row: CharacterDashboardRow, needle: str) -> bool:
        return (
            needle in row.character.casefold()
            or needle in row.pinyin.casefold()
            or needle in row.meaning.casefold()
        )
