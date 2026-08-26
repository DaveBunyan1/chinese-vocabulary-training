"""
Derive basic progress statistics from vocabulary and character knowledge records.
"""

from __future__ import annotations

from dataclasses import dataclass

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)


@dataclass(frozen=True, slots=True)
class StatusBreakdown:
    new: int
    learning: int
    known: int

    @property
    def total(self) -> int:
        return self.new + self.learning + self.known


@dataclass(frozen=True, slots=True)
class VocabularyProgressStats:
    by_status: StatusBreakdown
    total_successful_recalls: int
    total_failed_recalls: int
    total_times_seen: int
    items_practised: int  # successful_recalls + failed_recalls > 0


@dataclass(frozen=True, slots=True)
class CharacterProgressStats:
    by_status: StatusBreakdown
    total_successful_recognitions: int
    total_failed_recognitions: int
    total_times_seen: int
    items_practised: int


@dataclass(frozen=True, slots=True)
class ProgressStatsResult:
    vocabulary: VocabularyProgressStats
    characters: CharacterProgressStats


def _status_breakdown(counts: dict[KnowledgeStatus, int]) -> StatusBreakdown:
    def n(key: str | KnowledgeStatus) -> int:
        if key in counts:
            return int(counts[key])
        if isinstance(key, str):
            for k, v in counts.items():
                if getattr(k, "value", str(k)) == key:
                    return int(v)
        return 0

    return StatusBreakdown(
        new=n("new") or n(KnowledgeStatus.NEW),
        learning=n("learning") or n(KnowledgeStatus.LEARNING),
        known=n("known") or n(KnowledgeStatus.KNOWN),
    )


class GetProgressStats:
    def __init__(
        self,
        vocabulary_knowledge_repo: VocabularyKnowledgeRepository,
        character_knowledge_repo: CharacterKnowledgeRepository,
    ) -> None:
        self._vocab_repo = vocabulary_knowledge_repo
        self._char_repo = character_knowledge_repo

    async def execute(self, learner_id: LearnerId) -> ProgressStatsResult:
        vocab_counts = await self._vocab_repo.count_by_status(learner_id)
        char_counts = await self._char_repo.count_by_status(learner_id)

        vocab_all = await self._vocab_repo.get_all_for_learner(learner_id)
        char_all = await self._char_repo.get_all_for_learner(learner_id)

        vocab_success = sum(k.successful_recalls for k in vocab_all)
        vocab_failed = sum(k.failed_recalls for k in vocab_all)
        vocab_seen = sum(k.times_seen for k in vocab_all)
        vocab_practised = sum(
            1 for k in vocab_all if (k.successful_recalls + k.failed_recalls) > 0
        )

        char_success = sum(k.successful_recognitions for k in char_all)
        char_failed = sum(k.failed_recognitions for k in char_all)
        char_seen = sum(k.times_seen for k in char_all)
        char_practised = sum(
            1
            for k in char_all
            if (k.successful_recognitions + k.failed_recognitions) > 0
        )

        return ProgressStatsResult(
            vocabulary=VocabularyProgressStats(
                by_status=_status_breakdown(vocab_counts),
                total_successful_recalls=vocab_success,
                total_failed_recalls=vocab_failed,
                total_times_seen=vocab_seen,
                items_practised=vocab_practised,
            ),
            characters=CharacterProgressStats(
                by_status=_status_breakdown(char_counts),
                total_successful_recognitions=char_success,
                total_failed_recognitions=char_failed,
                total_times_seen=char_seen,
                items_practised=char_practised,
            ),
        )
