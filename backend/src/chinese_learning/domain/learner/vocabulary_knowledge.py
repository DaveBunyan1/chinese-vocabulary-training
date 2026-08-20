from dataclasses import dataclass
from datetime import datetime

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId


@dataclass(frozen=True, slots=True)
class VocabularyKnowledge:
    """
    Learner-specific knowledge state for one VocabularyItem.

    Designed to later add:
    - full attempt history (events)
    - spaced repetition fields
    - reading exposure counts
    - last seen in conversation, etc.
    without breaking existing rows.
    """

    learner_id: LearnerId
    vocabulary_id: VocabularyId
    status: KnowledgeStatus

    # Basic performance (can later be derived from events)
    successful_recalls: int = 0
    failed_recalls: int = 0

    # Exposure tracking (reading, conversation, etc.)
    times_seen: int = 0
    times_produced: int = 0

    # Timing
    first_seen_at: datetime | None = None
    last_practised_at: datetime | None = None
    last_seen_at: datetime | None = None

    # Future-proof slots (leave them None for now)
    next_review_at: datetime | None = None
    ease_factor: float | None = None  # for SM-2 later
    interval_days: float | None = None

    def __post_init__(self) -> None:
        if self.successful_recalls < 0 or self.failed_recalls < 0:
            raise ValueError("recall counts cannot be negative")
        if self.times_seen < 0 or self.times_produced < 0:
            raise ValueError("exposure counts cannot be negative")

    @property
    def total_attempts(self) -> int:
        return self.successful_recalls + self.failed_recalls

    # Immutable update helpers
    def with_success(self, at: datetime) -> VocabularyKnowledge:
        return VocabularyKnowledge(
            learner_id=self.learner_id,
            vocabulary_id=self.vocabulary_id,
            status=self._status_after_success(),
            successful_recalls=self.successful_recalls + 1,
            failed_recalls=self.failed_recalls,
            times_seen=self.times_seen,
            times_produced=self.times_produced + 1,
            first_seen_at=self.first_seen_at or at,
            last_practised_at=at,
            last_seen_at=at,
            next_review_at=self.next_review_at,
            ease_factor=self.ease_factor,
            interval_days=self.interval_days,
        )

    def with_failure(self, at: datetime) -> VocabularyKnowledge:
        return VocabularyKnowledge(
            learner_id=self.learner_id,
            vocabulary_id=self.vocabulary_id,
            status=self._status_after_failure(),
            successful_recalls=self.successful_recalls,
            failed_recalls=self.failed_recalls + 1,
            times_seen=self.times_seen,
            times_produced=self.times_produced + 1,
            first_seen_at=self.first_seen_at or at,
            last_practised_at=at,
            last_seen_at=at,
            next_review_at=self.next_review_at,
            ease_factor=self.ease_factor,
            interval_days=self.interval_days,
        )

    def with_exposure(self, at: datetime) -> VocabularyKnowledge:
        """Called when the item is seen in reading / conversation (not active recall)."""
        return VocabularyKnowledge(
            learner_id=self.learner_id,
            vocabulary_id=self.vocabulary_id,
            status=self.status,
            successful_recalls=self.successful_recalls,
            failed_recalls=self.failed_recalls,
            times_seen=self.times_seen + 1,
            times_produced=self.times_produced,
            first_seen_at=self.first_seen_at or at,
            last_practised_at=self.last_practised_at,
            last_seen_at=at,
            next_review_at=self.next_review_at,
            ease_factor=self.ease_factor,
            interval_days=self.interval_days,
        )

    def _status_after_success(self) -> KnowledgeStatus:
        if self.status is KnowledgeStatus.NEW:
            return KnowledgeStatus.LEARNING
        if (
            self.status is KnowledgeStatus.LEARNING
            and (self.successful_recalls + 1) >= 3
        ):
            return KnowledgeStatus.KNOWN
        return self.status

    def _status_after_failure(self) -> KnowledgeStatus:
        if self.status is KnowledgeStatus.KNOWN:
            return KnowledgeStatus.LEARNING
        return self.status
