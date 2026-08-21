from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge

NOW = datetime(2026, 8, 20, 12, 0, 0, tzinfo=UTC)


class TestVocabularyKnowledgeInvariants:
    def test_negative_successful_recalls_raises(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            make_vocabulary_knowledge(successful_recalls=-1)

    def test_negative_failed_recalls_raises(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            make_vocabulary_knowledge(failed_recalls=-1)

    def test_negative_times_seen_raises(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            make_vocabulary_knowledge(times_seen=-1)


class TestVocabularyKnowledgeWithSuccess:
    def test_new_becomes_learning_on_first_success(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(status=KnowledgeStatus.NEW)
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.successful_recalls == 1
        assert updated.failed_recalls == 0
        assert updated.times_produced == 1
        assert updated.first_seen_at == NOW
        assert updated.last_practised_at == NOW
        assert updated.last_seen_at == NOW

    def test_learning_stays_learning_before_threshold(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(
            status=KnowledgeStatus.LEARNING,
            successful_recalls=1,
        )
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.successful_recalls == 2

    def test_learning_becomes_known_after_three_successes(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(
            status=KnowledgeStatus.LEARNING,
            successful_recalls=2,
        )
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.KNOWN
        assert updated.successful_recalls == 3

    def test_known_stays_known_on_success(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(
            status=KnowledgeStatus.KNOWN,
            successful_recalls=5,
        )
        updated = knowledge.with_success(NOW)

        assert updated.status == KnowledgeStatus.KNOWN
        assert updated.successful_recalls == 6

    def test_original_instance_is_unchanged(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(status=KnowledgeStatus.NEW)
        knowledge.with_success(NOW)

        assert knowledge.status == KnowledgeStatus.NEW
        assert knowledge.successful_recalls == 0


class TestVocabularyKnowledgeWithFailure:
    def test_new_stays_new_on_failure(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(status=KnowledgeStatus.NEW)
        updated = knowledge.with_failure(NOW)

        assert updated.status == KnowledgeStatus.NEW
        assert updated.failed_recalls == 1
        assert updated.times_produced == 1

    def test_learning_stays_learning_on_failure(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(status=KnowledgeStatus.LEARNING)
        updated = knowledge.with_failure(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.failed_recalls == 1

    def test_known_drops_to_learning_on_failure(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(status=KnowledgeStatus.KNOWN)
        updated = knowledge.with_failure(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.failed_recalls == 1


class TestVocabularyKnowledgeWithExposure:
    def test_exposure_increments_times_seen_only(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(
            status=KnowledgeStatus.LEARNING,
            successful_recalls=2,
            times_seen=3,
        )
        updated = knowledge.with_exposure(NOW)

        assert updated.status == KnowledgeStatus.LEARNING
        assert updated.successful_recalls == 2
        assert updated.times_seen == 4
        assert updated.times_produced == 0
        assert updated.last_practised_at is None
        assert updated.last_seen_at == NOW
        assert updated.first_seen_at == NOW

    def test_first_seen_at_is_set_only_once(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        earlier = datetime(2026, 1, 1, tzinfo=UTC)
        knowledge = make_vocabulary_knowledge(first_seen_at=earlier, times_seen=1)

        updated = knowledge.with_exposure(NOW)

        assert updated.first_seen_at == earlier
        assert updated.times_seen == 2


class TestVocabularyKnowledgeProperties:
    def test_total_attempts(
        self, make_vocabulary_knowledge: Callable[..., VocabularyKnowledge]
    ) -> None:
        knowledge = make_vocabulary_knowledge(successful_recalls=4, failed_recalls=2)
        assert knowledge.total_attempts == 6
