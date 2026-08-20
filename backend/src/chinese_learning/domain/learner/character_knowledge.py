from dataclasses import dataclass
from datetime import datetime

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.text_analysis.character import Character


@dataclass(frozen=True, slots=True)
class CharacterKnowledge:
    """
    Learner-specific knowledge of a single Character.

    Intentionally parallel to VocabularyKnowledge so both systems evolve together.
    """

    learner_id: LearnerId
    character: Character  # Value Object – safe because Character is immutable
    status: KnowledgeStatus

    successful_recognitions: int = 0
    failed_recognitions: int = 0
    correct_pinyin_count: int = 0

    times_seen: int = 0
    first_seen_at: datetime | None = None
    last_practised_at: datetime | None = None
    last_seen_at: datetime | None = None

    # Future-proof
    next_review_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.successful_recognitions < 0 or self.failed_recognitions < 0:
            raise ValueError("recognition counts cannot be negative")
        if self.correct_pinyin_count < 0:
            raise ValueError("correct_pinyin_count cannot be negative")
        if self.times_seen < 0:
            raise ValueError("times_seen cannot be negative")

    @property
    def total_attempts(self) -> int:
        return self.successful_recognitions + self.failed_recognitions

    # Immutable update helpers
    def with_success(
        self,
        at: datetime,
        *,
        pinyin_correct: bool = True,
    ) -> CharacterKnowledge:
        return CharacterKnowledge(
            learner_id=self.learner_id,
            character=self.character,
            status=self._status_after_success(),
            successful_recognitions=self.successful_recognitions + 1,
            failed_recognitions=self.failed_recognitions,
            correct_pinyin_count=self.correct_pinyin_count
            + (1 if pinyin_correct else 0),
            times_seen=self.times_seen,
            first_seen_at=self.first_seen_at or at,
            last_practised_at=at,
            last_seen_at=at,
            next_review_at=self.next_review_at,
        )

    def with_failure(self, at: datetime) -> CharacterKnowledge:
        """Record a failed character recognition attempt."""
        return CharacterKnowledge(
            learner_id=self.learner_id,
            character=self.character,
            status=self._status_after_failure(),
            successful_recognitions=self.successful_recognitions,
            failed_recognitions=self.failed_recognitions + 1,
            correct_pinyin_count=self.correct_pinyin_count,
            times_seen=self.times_seen,
            first_seen_at=self.first_seen_at or at,
            last_practised_at=at,
            last_seen_at=at,
            next_review_at=self.next_review_at,
        )

    def with_exposure(self, at: datetime) -> CharacterKnowledge:
        """
        Record passive exposure (e.g. the character appeared in a reading text
        but the learner was not actively tested on it).
        """
        return CharacterKnowledge(
            learner_id=self.learner_id,
            character=self.character,
            status=self.status,
            successful_recognitions=self.successful_recognitions,
            failed_recognitions=self.failed_recognitions,
            correct_pinyin_count=self.correct_pinyin_count,
            times_seen=self.times_seen + 1,
            first_seen_at=self.first_seen_at or at,
            last_practised_at=self.last_practised_at,
            last_seen_at=at,
            next_review_at=self.next_review_at,
        )

    def _status_after_success(self) -> KnowledgeStatus:
        if self.status is KnowledgeStatus.NEW:
            return KnowledgeStatus.LEARNING
        if (
            self.status is KnowledgeStatus.LEARNING
            and (self.successful_recognitions + 1) >= 3
        ):
            return KnowledgeStatus.KNOWN
        return self.status

    def _status_after_failure(self) -> KnowledgeStatus:
        if self.status is KnowledgeStatus.KNOWN:
            return KnowledgeStatus.LEARNING
        return self.status
